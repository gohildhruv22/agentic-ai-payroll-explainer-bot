"""
Background autonomy engine for proactive agentic workflows.

Runs periodic jobs without user prompts while preserving existing API behavior.
"""
import json
import logging
import threading
import time
from datetime import datetime, timedelta

from config import (
    AUTONOMY_ENABLED,
    AUTONOMY_POLL_SECONDS,
    AUTONOMY_DISPUTE_REVIEW_MINUTES,
    AUTONOMY_PAYROLL_AUDIT_MINUTES,
    AUTONOMY_TAX_ADVISOR_MINUTES,
    AUTONOMY_JOB_MAX_RETRIES,
    AUTONOMY_JOB_FAILURE_COOLDOWN_SECONDS,
    AUTONOMY_JOB_FAILURE_STREAK_THRESHOLD,
    SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT,
    SLA_FAILED_JOBS_DAILY_LIMIT,
)
from database import SessionLocal
from models import AutonomousJobRun, DisputeTicket, Employee, SalaryRecord, SlaIncident, HumanApprovalRequest
from agents.dispute_review_agent import create_dispute_review_agent
from tools.notification_sender import notification_sender
from tools.tax_calculator import tax_calculator
from agents.agentic.pec_pipeline import run_pec_review
from config import REQUIRE_ADMIN_APPROVAL_ABOVE
from event_bus import publish_event, pull_pending_events, mark_event_processed, mark_event_failed

logger = logging.getLogger("payroll_bot.autonomy")


class AutonomyEngine:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self._last_run = {
            "auto_dispute_review": datetime.min,
            "payroll_consistency_audit": datetime.min,
            "tax_regime_advisor": datetime.min,
        }
        self._job_failures = {"auto_dispute_review": 0, "payroll_consistency_audit": 0, "tax_regime_advisor": 0}
        self._job_cooldown_until = {"auto_dispute_review": datetime.min, "payroll_consistency_audit": datetime.min, "tax_regime_advisor": datetime.min}

    def start(self):
        if not AUTONOMY_ENABLED:
            logger.info("Autonomy engine disabled via config.")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="autonomy-engine", daemon=True)
        self._thread.start()
        logger.info("Autonomy engine started.")

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Autonomy engine stopped.")

    def status(self) -> dict:
        return {
            "enabled": AUTONOMY_ENABLED,
            "running": bool(self._thread and self._thread.is_alive()),
            "poll_seconds": AUTONOMY_POLL_SECONDS,
            "last_run": {k: v.isoformat() if isinstance(v, datetime) else None for k, v in self._last_run.items()},
            "job_failures": self._job_failures,
            "job_cooldown_until": {k: v.isoformat() if isinstance(v, datetime) else None for k, v in self._job_cooldown_until.items()},
        }

    def run_job_now(self, job_name: str) -> dict:
        if job_name == "auto_dispute_review":
            return self._run_job("auto_dispute_review", self._auto_dispute_review)
        if job_name == "payroll_consistency_audit":
            return self._run_job("payroll_consistency_audit", self._payroll_consistency_audit)
        if job_name == "tax_regime_advisor":
            return self._run_job("tax_regime_advisor", self._tax_regime_advisor)
        return {"success": False, "error": f"Unknown job: {job_name}"}

    def _loop(self):
        while not self._stop_event.is_set():
            now = datetime.utcnow()
            try:
                self._consume_events()
                if now - self._last_run["auto_dispute_review"] >= timedelta(minutes=AUTONOMY_DISPUTE_REVIEW_MINUTES):
                    self._run_job("auto_dispute_review", self._auto_dispute_review)

                if now - self._last_run["payroll_consistency_audit"] >= timedelta(minutes=AUTONOMY_PAYROLL_AUDIT_MINUTES):
                    self._run_job("payroll_consistency_audit", self._payroll_consistency_audit)

                if now - self._last_run["tax_regime_advisor"] >= timedelta(minutes=AUTONOMY_TAX_ADVISOR_MINUTES):
                    self._run_job("tax_regime_advisor", self._tax_regime_advisor)
                self._check_sla_policies()
            except Exception as exc:
                logger.error("Autonomy loop error: %s", exc)
            time.sleep(max(10, AUTONOMY_POLL_SECONDS))

    def _run_job(self, job_name: str, func):
        if datetime.utcnow() < self._job_cooldown_until.get(job_name, datetime.min):
            return {
                "success": False,
                "job_name": job_name,
                "status": "cooldown",
                "summary": f"Job in cooldown until {self._job_cooldown_until[job_name].isoformat()}",
                "details": {},
            }
        start = datetime.utcnow()
        status = "success"
        summary = ""
        details = {}
        last_exc = None
        for attempt in range(AUTONOMY_JOB_MAX_RETRIES + 1):
            try:
                result = func()
                summary = result.get("summary", "completed")
                details = result
                status = "success"
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
                logger.exception("Autonomous job %s failed (attempt %s)", job_name, attempt + 1)
                if attempt < AUTONOMY_JOB_MAX_RETRIES:
                    time.sleep(min(2 ** attempt, 5))
        if last_exc is not None:
            status = "failed"
            summary = str(last_exc)
            details = {"success": False, "error": str(last_exc)}

        finish = datetime.utcnow()
        self._last_run[job_name] = finish
        self._log_job(job_name, status, summary, details, start, finish)
        if status == "success":
            self._job_failures[job_name] = 0
            publish_event("job_succeeded", {"job_name": job_name, "finished_at": finish.isoformat()})
        else:
            self._job_failures[job_name] = int(self._job_failures.get(job_name, 0)) + 1
            publish_event("job_failed", {"job_name": job_name, "error": summary})
            if self._job_failures[job_name] >= AUTONOMY_JOB_FAILURE_STREAK_THRESHOLD:
                self._job_cooldown_until[job_name] = datetime.utcnow() + timedelta(seconds=AUTONOMY_JOB_FAILURE_COOLDOWN_SECONDS)
                self._open_sla_incident(
                    incident_type="job_failure_streak",
                    severity="critical",
                    summary=f"{job_name} failed {self._job_failures[job_name]} times consecutively.",
                    details={"job_name": job_name, "cooldown_until": self._job_cooldown_until[job_name].isoformat()},
                )
        return {"success": status == "success", "job_name": job_name, "status": status, "summary": summary, "details": details}

    def _log_job(self, job_name: str, status: str, summary: str, details: dict, started_at: datetime, finished_at: datetime):
        db = SessionLocal()
        try:
            row = AutonomousJobRun(
                job_name=job_name,
                status=status,
                summary=summary,
                details_json=json.dumps(details),
                started_at=started_at,
                finished_at=finished_at,
            )
            db.add(row)
            db.commit()
        finally:
            db.close()

    def _auto_dispute_review(self):
        db = SessionLocal()
        try:
            tickets = db.query(DisputeTicket).filter(
                DisputeTicket.ai_reviewed == False,  # noqa: E712
                DisputeTicket.status.in_(["open", "in_review"]),
            ).all()
            if not tickets:
                return {"summary": "No pending disputes for AI review", "reviewed": 0}

            agent = create_dispute_review_agent()
            reviewed = 0
            escalated = 0
            for ticket in tickets:
                employee = db.query(Employee).filter(Employee.id == ticket.employee_id).first()
                if not employee:
                    continue
                prompt = (
                    f"Review dispute ticket {ticket.ticket_id}.\n"
                    f"Category: {ticket.category}\n"
                    f"Description: {ticket.description}\n"
                    f"Expected: {ticket.expected_amount}\n"
                    f"Actual: {ticket.actual_amount}\n"
                    f"Discrepancy: {ticket.discrepancy_amount}\n"
                    f"Employee ID: {employee.id}"
                )
                context = {
                    "employee": {
                        "id": employee.id,
                        "name": employee.name,
                        "department": employee.department,
                        "designation": employee.designation,
                        "location": employee.location,
                        "city_tier": employee.city_tier,
                        "annual_ctc": employee.annual_ctc,
                        "tax_regime": employee.tax_regime,
                        "rent_paid_monthly": employee.rent_paid_monthly,
                    },
                    "current_date": datetime.utcnow().strftime("%Y-%m-%d"),
                }
                result = agent.run(user_message=prompt, context=context)
                text = result.get("response", "")
                pec = run_pec_review(agent, prompt, context=context)
                final_text = pec.get("final_response") or text
                verdict = _extract_verdict(final_text)
                discrepancy_abs = abs(float(ticket.discrepancy_amount or 0))
                risk_score = float(pec.get("risk_score", 0.5))

                ticket.ai_reviewed = True
                ticket.ai_verdict = verdict
                ticket.ai_analysis = (
                    f"{final_text}\n\n[PEC Critic]\n{pec.get('critic', '')}\nRisk Score: {risk_score:.2f}"
                )[:4000]
                ticket.ai_reviewed_at = datetime.utcnow()

                require_approval = (
                    verdict != "resolved_invalid"
                    or discrepancy_abs >= REQUIRE_ADMIN_APPROVAL_ABOVE
                    or risk_score >= 0.6
                )

                if verdict == "resolved_invalid" and not require_approval:
                    ticket.status = "resolved"
                    ticket.resolved_at = datetime.utcnow()
                    ticket.resolution_notes = final_text[:2000]
                else:
                    ticket.status = "awaiting_approval"
                    _upsert_approval_request(
                        db=db,
                        request_type="dispute_resolution",
                        reference_id=ticket.ticket_id,
                        employee_id=ticket.employee_id,
                        reason="Autonomous dispute review requires admin sign-off.",
                        risk_score=risk_score,
                        proposed_action=f"Verdict={verdict}, discrepancy={discrepancy_abs:.2f}",
                    )
                    escalated += 1

                notification_sender(
                    employee_id=ticket.employee_id,
                    subject=f"Update on dispute {ticket.ticket_id}",
                    body=(
                        f"Your dispute received a preliminary AI review. Current status: {ticket.status}. "
                        "Final decision is pending HR/admin approval."
                    ),
                )
                reviewed += 1

            db.commit()
            return {"summary": f"Auto-reviewed {reviewed} disputes ({escalated} escalated)", "reviewed": reviewed, "escalated": escalated}
        finally:
            db.close()

    def _payroll_consistency_audit(self):
        db = SessionLocal()
        try:
            records = db.query(SalaryRecord).all()
            if not records:
                return {"summary": "No salary records found", "issues": 0}

            issues = []
            for rec in records:
                ded_expected = round((rec.pf_employee or 0) + (rec.esic_employee or 0) + (rec.professional_tax or 0) + (rec.tds or 0), 2)
                net_expected = round((rec.gross_pay or 0) - ded_expected, 2)
                ded_gap = abs(round((rec.total_deductions or 0) - ded_expected, 2))
                net_gap = abs(round((rec.net_pay or 0) - net_expected, 2))
                if ded_gap > 2 or net_gap > 2:
                    issues.append({"employee_id": rec.employee_id, "month": rec.month, "deduction_gap": ded_gap, "net_gap": net_gap})

            for issue in issues[:50]:
                ref = f"{issue['employee_id']}:{issue['month']}"
                risk = min(1.0, 0.2 + float(issue["deduction_gap"] + issue["net_gap"]) / 50.0)
                _upsert_approval_request(
                    db=db,
                    request_type="payroll_anomaly",
                    reference_id=ref,
                    employee_id=issue["employee_id"],
                    reason="Payroll consistency audit detected mismatch.",
                    risk_score=risk,
                    proposed_action=f"Investigate payroll record for {issue['month']} and decide correction path.",
                )
                notification_sender(
                    employee_id=issue["employee_id"],
                    subject=f"Payroll re-validation in progress ({issue['month']})",
                    body=(
                        "An automatic payroll consistency check flagged a potential mismatch. "
                        "This is preliminary and under HR/admin review."
                    ),
                )

            return {"summary": f"Audited {len(records)} salary records, found {len(issues)} anomalies", "audited": len(records), "issues": issues[:200]}
        finally:
            db.close()

    def _tax_regime_advisor(self):
        db = SessionLocal()
        try:
            employees = db.query(Employee).all()
            suggestions = 0
            for emp in employees:
                annual = float(emp.annual_ctc or 0)
                if annual <= 0:
                    continue
                basic_annual = annual * 0.4
                hra_annual = annual * 0.2
                calc = tax_calculator(
                    annual_gross_income=annual,
                    basic_annual=basic_annual,
                    hra_annual=hra_annual,
                    rent_paid_annual=float(emp.rent_paid_monthly or 0) * 12,
                    city_tier=emp.city_tier or "metro",
                    regime="both",
                )
                tax_data = calc.get("tax_calculation", {})
                recommendation = tax_data.get("recommendation")
                savings = float(tax_data.get("savings") or 0)
                if recommendation and savings >= 10000 and recommendation.lower().startswith("new") and (emp.tax_regime or "").lower() == "old":
                    _upsert_approval_request(
                        db=db,
                        request_type="tax_recommendation",
                        reference_id=f"{emp.id}:{datetime.utcnow().strftime('%Y-%m')}",
                        employee_id=emp.id,
                        reason="Autonomous tax advisor generated recommendation requiring HR oversight.",
                        risk_score=min(1.0, savings / 100000.0),
                        proposed_action=f"Recommend switching regime to {recommendation}; estimated savings ₹{savings:,.0f}.",
                    )
                    notification_sender(
                        employee_id=emp.id,
                        subject="Autonomous tax recommendation",
                        body=(
                            f"Preliminary advisory: you may save about ₹{savings:,.0f}/year by switching to {recommendation}. "
                            "Please wait for HR/admin confirmation before making final declarations."
                        ),
                    )
                    suggestions += 1
            return {"summary": f"Tax advisor evaluated {len(employees)} employees, sent {suggestions} proactive recommendations", "suggestions": suggestions}
        finally:
            db.close()

    def _consume_events(self):
        events = pull_pending_events(limit=20)
        for ev in events:
            try:
                et = ev.get("event_type")
                payload = ev.get("payload") or {}
                if et == "manual_run_job":
                    job_name = payload.get("job_name")
                    if job_name:
                        self.run_job_now(job_name)
                elif et == "recheck_dispute":
                    # Schedule dispute review loop sooner by backdating marker.
                    self._last_run["auto_dispute_review"] = datetime.min
                elif et == "recheck_payroll_audit":
                    self._last_run["payroll_consistency_audit"] = datetime.min
                mark_event_processed(ev["id"])
            except Exception as exc:
                mark_event_failed(ev["id"], str(exc))

    def _check_sla_policies(self):
        db = SessionLocal()
        try:
            today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
            failed_today = db.query(AutonomousJobRun).filter(
                AutonomousJobRun.started_at >= today_start,
                AutonomousJobRun.status == "failed",
            ).count()
            high_risk_pending = db.query(HumanApprovalRequest).filter(
                HumanApprovalRequest.status == "pending",
                HumanApprovalRequest.risk_score >= 0.7,
            ).count()
            if failed_today > SLA_FAILED_JOBS_DAILY_LIMIT:
                self._open_sla_incident(
                    incident_type="sla_failed_jobs",
                    severity="critical",
                    summary=f"Daily failed jobs exceeded SLA ({failed_today}/{SLA_FAILED_JOBS_DAILY_LIMIT}).",
                    details={"failed_today": failed_today},
                    db=db,
                )
            if high_risk_pending > SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT:
                self._open_sla_incident(
                    incident_type="sla_high_risk_approvals",
                    severity="warning",
                    summary=f"High-risk pending approvals exceeded SLA ({high_risk_pending}/{SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT}).",
                    details={"high_risk_pending": high_risk_pending},
                    db=db,
                )
            self._auto_resolve_sla_incidents(
                db=db,
                failed_today=failed_today,
                high_risk_pending=high_risk_pending,
            )
        finally:
            db.close()

    def _open_sla_incident(self, incident_type: str, severity: str, summary: str, details: dict, db=None):
        owns_session = db is None
        db = db or SessionLocal()
        try:
            existing = db.query(SlaIncident).filter(
                SlaIncident.incident_type == incident_type,
                SlaIncident.status == "open",
            ).first()
            if existing:
                return
            row = SlaIncident(
                incident_type=incident_type,
                severity=severity,
                summary=summary,
                details_json=json.dumps(details or {}),
                status="open",
                created_at=datetime.utcnow(),
            )
            db.add(row)
            db.commit()
        finally:
            if owns_session:
                db.close()

    def _auto_resolve_sla_incidents(self, db, failed_today: int, high_risk_pending: int):
        # If metrics are back within thresholds, auto-resolve stale open incidents.
        now = datetime.utcnow()
        if failed_today <= SLA_FAILED_JOBS_DAILY_LIMIT:
            row = db.query(SlaIncident).filter(
                SlaIncident.incident_type == "sla_failed_jobs",
                SlaIncident.status.in_(["open", "acknowledged"]),
            ).first()
            if row:
                row.status = "resolved"
                row.resolved_at = now
                row.summary = f"{row.summary} | Auto-resolved after recovery ({failed_today} failed jobs)."
        if high_risk_pending <= SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT:
            row = db.query(SlaIncident).filter(
                SlaIncident.incident_type == "sla_high_risk_approvals",
                SlaIncident.status.in_(["open", "acknowledged"]),
            ).first()
            if row:
                row.status = "resolved"
                row.resolved_at = now
                row.summary = f"{row.summary} | Auto-resolved after recovery ({high_risk_pending} pending high-risk approvals)."
        db.commit()


def _extract_verdict(ai_response: str) -> str:
    text = (ai_response or "").lower()
    if "resolved_invalid" in text:
        return "resolved_invalid"
    if "resolved_valid" in text:
        return "resolved_valid"
    return "escalated"


def _upsert_approval_request(
    db,
    request_type: str,
    reference_id: str,
    employee_id: int,
    reason: str,
    risk_score: float,
    proposed_action: str,
):
    req = db.query(HumanApprovalRequest).filter(
        HumanApprovalRequest.request_type == request_type,
        HumanApprovalRequest.reference_id == reference_id,
        HumanApprovalRequest.status == "pending",
    ).first()
    if req:
        req.risk_score = max(float(req.risk_score or 0), float(risk_score))
        req.reason = reason
        req.proposed_action = proposed_action
        return req
    req = HumanApprovalRequest(
        request_type=request_type,
        reference_id=reference_id,
        employee_id=employee_id,
        reason=reason,
        risk_score=risk_score,
        proposed_action=proposed_action,
        status="pending",
    )
    db.add(req)
    return req

