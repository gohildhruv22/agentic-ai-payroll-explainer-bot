"""
Admin endpoints for autonomy engine status and job controls.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import require_role
from database import SessionLocal
from models import AutonomousJobRun, HumanApprovalRequest, DisputeTicket, AutonomousEvent, SlaIncident
from config import SLA_FAILED_JOBS_DAILY_LIMIT, SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT
from event_bus import publish_event
import runtime_state

router = APIRouter(prefix="/api/autonomy", tags=["Autonomy"])


class RunJobRequest(BaseModel):
    job_name: str


class ApprovalDecisionRequest(BaseModel):
    decision: str  # approved, rejected
    notes: str = ""


class EventPublishRequest(BaseModel):
    event_type: str
    payload: dict = {}


class SlaIncidentDecisionRequest(BaseModel):
    decision: str  # acknowledge, resolve
    notes: str = ""


@router.get("/status")
def autonomy_status(current_user: dict = Depends(require_role(["admin", "hr_manager"]))):
    if not runtime_state.autonomy_engine:
        raise HTTPException(status_code=503, detail="Autonomy engine is not initialized")
    return runtime_state.autonomy_engine.status()


@router.get("/phase2-health")
def autonomy_phase2_health(current_user: dict = Depends(require_role(["admin", "hr_manager"]))):
    db = SessionLocal()
    try:
        pending = db.query(HumanApprovalRequest).filter(HumanApprovalRequest.status == "pending").count()
        high_risk = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending",
            HumanApprovalRequest.risk_score >= 0.7
        ).count()
        dispute_pending = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending",
            HumanApprovalRequest.request_type == "dispute_resolution"
        ).count()
        return {
            "phase": "2",
            "status": "healthy",
            "approvals": {
                "pending_total": pending,
                "pending_high_risk": high_risk,
                "pending_dispute_resolution": dispute_pending,
            },
            "engine": runtime_state.autonomy_engine.status() if runtime_state.autonomy_engine else {"running": False},
        }
    finally:
        db.close()


@router.get("/phase3-health")
def autonomy_phase3_health(current_user: dict = Depends(require_role(["admin", "hr_manager"]))):
    db = SessionLocal()
    try:
        from datetime import datetime
        today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())

        pending_approvals = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending"
        ).count()
        pending_high_risk_approvals = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending",
            HumanApprovalRequest.risk_score >= 0.7,
        ).count()
        pending_events = db.query(AutonomousEvent).filter(
            AutonomousEvent.status == "pending"
        ).count()
        failed_events_today = db.query(AutonomousEvent).filter(
            AutonomousEvent.status == "failed",
            AutonomousEvent.created_at >= today_start,
        ).count()
        failed_jobs_today = db.query(AutonomousJobRun).filter(
            AutonomousJobRun.status == "failed",
            AutonomousJobRun.started_at >= today_start,
        ).count()
        open_sla_incidents = db.query(SlaIncident).filter(
            SlaIncident.status.in_(["open", "acknowledged"])
        ).count()
        critical_open_sla = db.query(SlaIncident).filter(
            SlaIncident.status.in_(["open", "acknowledged"]),
            SlaIncident.severity == "critical",
        ).count()

        engine_status = runtime_state.autonomy_engine.status() if runtime_state.autonomy_engine else {"running": False}
        engine_running = bool(engine_status.get("running"))

        checks = [
            {
                "id": "engine_running",
                "ok": engine_running,
                "message": "Autonomy engine is running." if engine_running else "Autonomy engine is not running.",
            },
            {
                "id": "failed_jobs_sla",
                "ok": failed_jobs_today <= SLA_FAILED_JOBS_DAILY_LIMIT,
                "message": f"Failed jobs today: {failed_jobs_today}/{SLA_FAILED_JOBS_DAILY_LIMIT}",
            },
            {
                "id": "high_risk_approvals_sla",
                "ok": pending_high_risk_approvals <= SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT,
                "message": f"High-risk pending approvals: {pending_high_risk_approvals}/{SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT}",
            },
            {
                "id": "critical_incidents",
                "ok": critical_open_sla == 0,
                "message": f"Critical open SLA incidents: {critical_open_sla}",
            },
            {
                "id": "event_backlog",
                "ok": pending_events <= 100,
                "message": f"Pending event backlog: {pending_events}",
            },
        ]

        passed = sum(1 for c in checks if c["ok"])
        score = round((passed / len(checks)) * 100) if checks else 0
        status = "healthy" if score >= 80 else ("degraded" if score >= 50 else "critical")

        actions = []
        if not engine_running:
            actions.append("Restart backend service and verify autonomy engine startup logs.")
        if failed_jobs_today > SLA_FAILED_JOBS_DAILY_LIMIT:
            actions.append("Inspect /api/autonomy/runs for repeated failures and reduce load or increase retry resilience.")
        if pending_high_risk_approvals > SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT:
            actions.append("Process high-risk approvals from /api/autonomy/approvals urgently.")
        if critical_open_sla > 0:
            actions.append("Acknowledge and resolve critical SLA incidents via /api/autonomy/sla/{incident_id}/decision.")
        if pending_events > 100:
            actions.append("Check event handlers and worker throughput; review /api/autonomy/events.")

        return {
            "phase": "3",
            "status": status,
            "readiness_score": score,
            "checks": checks,
            "metrics": {
                "pending_approvals": pending_approvals,
                "pending_high_risk_approvals": pending_high_risk_approvals,
                "pending_events": pending_events,
                "failed_events_today": failed_events_today,
                "failed_jobs_today": failed_jobs_today,
                "open_sla_incidents": open_sla_incidents,
                "critical_open_sla_incidents": critical_open_sla,
            },
            "actions": actions,
            "engine": engine_status,
        }
    finally:
        db.close()


@router.post("/run")
def run_autonomy_job(payload: RunJobRequest, current_user: dict = Depends(require_role(["admin"]))):
    if not runtime_state.autonomy_engine:
        raise HTTPException(status_code=503, detail="Autonomy engine is not initialized")
    result = runtime_state.autonomy_engine.run_job_now(payload.job_name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error") or result.get("summary"))
    return result


@router.post("/events")
def publish_autonomy_event(payload: EventPublishRequest, current_user: dict = Depends(require_role(["admin"]))):
    result = publish_event(payload.event_type, payload.payload or {})
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unable to publish event"))
    return {"message": "Event queued", **result}


@router.get("/events")
def list_autonomy_events(current_user: dict = Depends(require_role(["admin", "hr_manager"]))):
    db = SessionLocal()
    try:
        rows = db.query(AutonomousEvent).order_by(AutonomousEvent.created_at.desc()).limit(200).all()
        return {
            "events": [
                {
                    "id": r.id,
                    "event_type": r.event_type,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "processed_at": r.processed_at.isoformat() if r.processed_at else None,
                    "error": r.error,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.get("/runs")
def list_autonomy_runs(current_user: dict = Depends(require_role(["admin", "hr_manager"]))):
    db = SessionLocal()
    try:
        rows = db.query(AutonomousJobRun).order_by(AutonomousJobRun.started_at.desc()).limit(100).all()
        return {
            "runs": [
                {
                    "id": r.id,
                    "job_name": r.job_name,
                    "status": r.status,
                    "summary": r.summary,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.get("/approvals")
def list_autonomy_approvals(current_user: dict = Depends(require_role(["admin", "hr_manager"]))):
    db = SessionLocal()
    try:
        rows = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending"
        ).order_by(HumanApprovalRequest.requested_at.desc()).limit(200).all()
        return {
            "approvals": [
                {
                    "id": r.id,
                    "request_type": r.request_type,
                    "reference_id": r.reference_id,
                    "employee_id": r.employee_id,
                    "reason": r.reason,
                    "risk_score": r.risk_score,
                    "proposed_action": r.proposed_action,
                    "requested_at": r.requested_at.isoformat() if r.requested_at else None,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.post("/approvals/{approval_id}/decision")
def decide_autonomy_approval(
    approval_id: int,
    payload: ApprovalDecisionRequest,
    current_user: dict = Depends(require_role(["admin"])),
):
    decision = (payload.decision or "").strip().lower()
    if decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")

    db = SessionLocal()
    try:
        req = db.query(HumanApprovalRequest).filter(HumanApprovalRequest.id == approval_id).first()
        if not req:
            raise HTTPException(status_code=404, detail="Approval request not found")
        if req.status != "pending":
            return {"message": "Approval request already decided", "approval_id": req.id, "status": req.status}

        req.status = decision
        req.reviewed_by = current_user["id"]
        from datetime import datetime
        req.reviewed_at = datetime.utcnow()
        req.review_notes = payload.notes or ""

        # Apply decision side-effects for known approval types.
        if req.request_type == "dispute_resolution":
            ticket = db.query(DisputeTicket).filter(DisputeTicket.ticket_id == req.reference_id).first()
            if ticket:
                ticket.admin_reviewed = True
                ticket.admin_reviewed_at = datetime.utcnow()
                ticket.admin_notes = payload.notes or ""
                if decision == "approved":
                    ticket.status = "resolved"
                    ticket.admin_action = "approved"
                    ticket.resolved_at = datetime.utcnow()
                else:
                    ticket.status = "in_review"
                    ticket.admin_action = "rejected"
        elif req.request_type in ("payroll_anomaly", "tax_recommendation"):
            # Trigger a follow-up autonomous event after approval decisions.
            if req.request_type == "payroll_anomaly":
                publish_event("recheck_payroll_audit", {"reference_id": req.reference_id, "decision": decision})
            else:
                publish_event("manual_run_job", {"job_name": "tax_regime_advisor", "decision": decision})
        db.commit()

        return {
            "message": "Approval decision recorded",
            "approval": {
                "id": req.id,
                "request_type": req.request_type,
                "reference_id": req.reference_id,
                "status": req.status,
                "reviewed_by": req.reviewed_by,
                "reviewed_at": req.reviewed_at.isoformat() if req.reviewed_at else None,
                "review_notes": req.review_notes,
            },
        }
    finally:
        db.close()


@router.get("/sla")
def get_sla_incidents(current_user: dict = Depends(require_role(["admin", "hr_manager"]))):
    db = SessionLocal()
    try:
        rows = db.query(SlaIncident).order_by(SlaIncident.created_at.desc()).limit(200).all()
        return {
            "incidents": [
                {
                    "id": r.id,
                    "incident_type": r.incident_type,
                    "severity": r.severity,
                    "summary": r.summary,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.post("/sla/{incident_id}/decision")
def decide_sla_incident(
    incident_id: int,
    payload: SlaIncidentDecisionRequest,
    current_user: dict = Depends(require_role(["admin"])),
):
    decision = (payload.decision or "").strip().lower()
    if decision not in ("acknowledge", "resolve"):
        raise HTTPException(status_code=400, detail="decision must be 'acknowledge' or 'resolve'")

    db = SessionLocal()
    try:
        row = db.query(SlaIncident).filter(SlaIncident.id == incident_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="SLA incident not found")

        from datetime import datetime
        note = (payload.notes or "").strip()
        note_text = f"[{datetime.utcnow().isoformat()}] admin#{current_user['id']} {decision}: {note}"
        existing_details = row.details_json or ""
        row.details_json = (existing_details + "\n" + note_text).strip()

        if decision == "acknowledge":
            if row.status == "open":
                row.status = "acknowledged"
        else:
            row.status = "resolved"
            row.resolved_at = datetime.utcnow()

        db.commit()
        return {
            "message": "SLA incident updated",
            "incident": {
                "id": row.id,
                "incident_type": row.incident_type,
                "status": row.status,
                "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
            },
        }
    finally:
        db.close()

