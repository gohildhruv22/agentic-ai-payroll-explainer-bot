"""
Dispute tickets API: employees file salary issues; HR/admin review; admin AI-escalation queue.

Creates tickets, runs optional AI review agent, and supports status / admin workflow updates.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import re
from auth import get_current_user, require_role
from database import SessionLocal
from models import DisputeTicket, Employee, HumanApprovalRequest
from agents.dispute_review_agent import create_dispute_review_agent
from tools.employee_profile_fetch import employee_profile_fetch
from tools.deterministic_payroll_check import deterministic_payroll_check
from agents.agentic.pec_pipeline import run_pec_review
from config import AUTO_APPROVAL_MAX_DISCREPANCY, REQUIRE_ADMIN_APPROVAL_ABOVE

router = APIRouter(prefix="/api/disputes", tags=["Disputes"])


class DisputeUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    priority: Optional[str] = None


class AdminReviewAction(BaseModel):
    action: str  # approved, rejected, modified
    admin_notes: Optional[str] = None
    new_status: Optional[str] = None


@router.get("/my")
def get_my_disputes(current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        tickets = db.query(DisputeTicket).filter(
            DisputeTicket.employee_id == current_user["id"]
        ).order_by(DisputeTicket.created_at.desc()).all()

        return {"disputes": [_ticket_to_dict(t) for t in tickets]}
    finally:
        db.close()


@router.get("")
def get_all_disputes(current_user: dict = Depends(require_role(["hr_manager", "admin"]))):
    db = SessionLocal()
    try:
        tickets = db.query(DisputeTicket).order_by(DisputeTicket.created_at.desc()).all()
        result = []
        for t in tickets:
            emp = db.query(Employee).filter(Employee.id == t.employee_id).first()
            d = _ticket_to_dict(t)
            d["employee_name"] = emp.name if emp else "Unknown"
            d["employee_email"] = emp.email if emp else "N/A"
            result.append(d)
        return {"disputes": result}
    finally:
        db.close()


@router.get("/admin/pending")
def get_admin_pending_disputes(current_user: dict = Depends(require_role(["admin"]))):
    """Get disputes that need admin review: AI-escalated or AI-resolved-valid."""
    db = SessionLocal()
    try:
        tickets = db.query(DisputeTicket).filter(
            DisputeTicket.ai_reviewed == True,
            DisputeTicket.admin_reviewed == False,
            DisputeTicket.status.in_(["escalated", "awaiting_approval", "in_review"]),
        ).order_by(DisputeTicket.created_at.desc()).all()

        result = []
        for t in tickets:
            emp = db.query(Employee).filter(Employee.id == t.employee_id).first()
            d = _ticket_to_dict(t)
            d["employee_name"] = emp.name if emp else "Unknown"
            d["employee_email"] = emp.email if emp else "N/A"
            result.append(d)
        return {"disputes": result}
    finally:
        db.close()


@router.get("/admin/approvals")
def get_pending_approvals(current_user: dict = Depends(require_role(["admin"]))):
    db = SessionLocal()
    try:
        rows = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending"
        ).order_by(HumanApprovalRequest.requested_at.desc()).all()
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
                    "status": r.status,
                    "requested_at": r.requested_at.isoformat() if r.requested_at else None,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.get("/admin/all")
def get_admin_all_disputes(current_user: dict = Depends(require_role(["admin"]))):
    """Admin view: all disputes with full AI + admin review info."""
    db = SessionLocal()
    try:
        tickets = db.query(DisputeTicket).order_by(DisputeTicket.created_at.desc()).all()
        result = []
        for t in tickets:
            emp = db.query(Employee).filter(Employee.id == t.employee_id).first()
            d = _ticket_to_dict(t)
            d["employee_name"] = emp.name if emp else "Unknown"
            d["employee_email"] = emp.email if emp else "N/A"
            result.append(d)
        return {"disputes": result}
    finally:
        db.close()


@router.get("/admin/stats")
def get_dispute_stats(current_user: dict = Depends(require_role(["admin"]))):
    """Admin dispute stats."""
    db = SessionLocal()
    try:
        total = db.query(DisputeTicket).count()
        open_count = db.query(DisputeTicket).filter(DisputeTicket.status == "open").count()
        ai_reviewed = db.query(DisputeTicket).filter(DisputeTicket.ai_reviewed == True).count()
        ai_escalated = db.query(DisputeTicket).filter(DisputeTicket.ai_verdict == "escalated").count()
        ai_resolved_valid = db.query(DisputeTicket).filter(DisputeTicket.ai_verdict == "resolved_valid").count()
        ai_resolved_invalid = db.query(DisputeTicket).filter(DisputeTicket.ai_verdict == "resolved_invalid").count()
        admin_reviewed = db.query(DisputeTicket).filter(DisputeTicket.admin_reviewed == True).count()
        pending_admin = db.query(DisputeTicket).filter(
            DisputeTicket.ai_reviewed == True, DisputeTicket.admin_reviewed == False
        ).count()
        awaiting_approval = db.query(DisputeTicket).filter(
            DisputeTicket.status == "awaiting_approval"
        ).count()
        pending_approval_requests = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending"
        ).count()

        return {
            "total": total,
            "open": open_count,
            "ai_reviewed": ai_reviewed,
            "ai_escalated": ai_escalated,
            "ai_resolved_valid": ai_resolved_valid,
            "ai_resolved_invalid": ai_resolved_invalid,
            "admin_reviewed": admin_reviewed,
            "pending_admin_review": pending_admin,
            "awaiting_approval": awaiting_approval,
            "pending_approval_requests": pending_approval_requests,
        }
    finally:
        db.close()


@router.post("/ai-review/{ticket_id}")
def ai_review_dispute(ticket_id: str, current_user: dict = Depends(require_role(["hr_manager", "admin"]))):
    """Trigger AI review of a specific dispute ticket."""
    db = SessionLocal()
    try:
        ticket = db.query(DisputeTicket).filter(DisputeTicket.ticket_id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Dispute ticket not found")

        emp = db.query(Employee).filter(Employee.id == ticket.employee_id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        review_prompt = (
            "Review this dispute ticket:\n"
            f"- Ticket ID: {ticket.ticket_id}\n"
            f"- Employee: {emp.name} (ID: {emp.id})\n"
            f"- Category: {ticket.category}\n"
            f"- Description: {ticket.description}\n"
            f"- Priority: {ticket.priority}\n"
        )
        if ticket.expected_amount is not None:
            review_prompt += f"- Expected Amount: ₹{ticket.expected_amount:,.0f}\n"
        if ticket.actual_amount is not None:
            review_prompt += f"- Actual Amount: ₹{ticket.actual_amount:,.0f}\n"
        if ticket.discrepancy_amount is not None:
            review_prompt += f"- Discrepancy: ₹{ticket.discrepancy_amount:,.0f}\n"
        review_prompt += (
            f"\nEmployee details: CTC ₹{emp.annual_ctc:,.0f}, Location: {emp.location} ({emp.city_tier}), "
            f"Tax Regime: {emp.tax_regime}, Monthly Rent: ₹{emp.rent_paid_monthly:,.0f}\n"
            "\nPlease investigate and provide your verdict."
        )

        agent = create_dispute_review_agent()
        context = {
            "employee": {
                "id": emp.id, "name": emp.name, "department": emp.department,
                "designation": emp.designation, "location": emp.location,
                "city_tier": emp.city_tier, "annual_ctc": emp.annual_ctc,
                "tax_regime": emp.tax_regime, "rent_paid_monthly": emp.rent_paid_monthly,
            },
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        }

        result = agent.run(user_message=review_prompt, context=context)
        pec = run_pec_review(agent, review_prompt, context=context)
        ai_response = pec.get("final_response") or result.get("response", "Unable to complete review")
        verdict = _extract_verdict(ai_response)
        month_hint = _extract_month_from_text(ticket.description)
        critic = deterministic_payroll_check(ticket.employee_id, month_hint) if month_hint else {"success": False}
        discrepancy_abs = abs(float(ticket.discrepancy_amount or 0))
        risk_score = max(float(pec.get("risk_score", 0.5)), _heuristic_risk(ticket, critic))

        # Critic guardrail: if deterministic mismatch exists, force escalation for human review.
        if critic.get("success") and not critic.get("is_consistent"):
            verdict = "escalated"
            ai_response += (
                "\n\nCritic note: deterministic payroll validation found a mismatch in stored "
                f"net/deduction values (net gap: {critic.get('net_gap')}, deduction gap: {critic.get('total_gap')})."
            )

        ticket.ai_reviewed = True
        ticket.ai_verdict = verdict
        ticket.ai_analysis = ai_response
        ticket.ai_reviewed_at = datetime.utcnow()

        ai_response += (
            f"\n\n[PEC]\nPlan:\n{pec.get('planner', '')}\n\nCritic:\n{pec.get('critic', '')}\n"
            f"Risk Score: {risk_score:.2f}"
        )

        require_admin = (
            verdict != "resolved_invalid"
            or discrepancy_abs >= REQUIRE_ADMIN_APPROVAL_ABOVE
            or risk_score >= 0.6
        )

        if verdict == "resolved_invalid" and not require_admin and discrepancy_abs <= AUTO_APPROVAL_MAX_DISCREPANCY:
            ticket.status = "resolved"
            ticket.resolution_notes = ai_response
            ticket.resolved_at = datetime.utcnow()
        elif require_admin:
            ticket.status = "awaiting_approval"
            _create_or_refresh_approval_request(
                db=db,
                ticket=ticket,
                risk_score=risk_score,
                proposed_action=f"AI verdict: {verdict}. discrepancy={discrepancy_abs:.2f}",
                reason="High-impact or low-confidence dispute outcome requires admin approval.",
            )
        elif verdict == "escalated":
            ticket.status = "escalated"
        elif verdict == "resolved_valid":
            ticket.status = "escalated"  # Needs admin to confirm and take action

        db.commit()
        db.refresh(ticket)

        return {
            "message": f"AI review complete for {ticket_id}",
            "verdict": verdict,
            "analysis": ai_response,
            "dispute": _ticket_to_dict(ticket),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI review failed: {str(e)}")
    finally:
        db.close()


@router.post("/ai-review-all")
def ai_review_all_open(current_user: dict = Depends(require_role(["admin"]))):
    """Trigger AI review on all open/unreviewed disputes."""
    db = SessionLocal()
    try:
        open_tickets = db.query(DisputeTicket).filter(
            DisputeTicket.ai_reviewed == False,
            DisputeTicket.status.in_(["open", "in_review"]),
        ).all()

        results = []
        for ticket in open_tickets:
            try:
                db.close()
                res = ai_review_dispute(ticket.ticket_id, current_user)
                results.append({"ticket_id": ticket.ticket_id, "verdict": res.get("verdict"), "success": True})
            except Exception as e:
                results.append({"ticket_id": ticket.ticket_id, "error": str(e), "success": False})

        return {"reviewed": len(results), "results": results}
    finally:
        db.close()


@router.post("/admin-review/{ticket_id}")
def admin_review_dispute(
    ticket_id: str,
    review: AdminReviewAction,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Admin reviews an AI-analyzed dispute and takes final action."""
    db = SessionLocal()
    try:
        ticket = db.query(DisputeTicket).filter(DisputeTicket.ticket_id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Dispute ticket not found")

        ticket.admin_reviewed = True
        ticket.admin_action = review.action
        ticket.admin_notes = review.admin_notes
        ticket.admin_reviewed_at = datetime.utcnow()

        if review.action == "approved":
            ticket.status = "resolved"
            ticket.resolved_at = datetime.utcnow()
            if review.admin_notes:
                ticket.resolution_notes = (ticket.resolution_notes or "") + f"\n\nAdmin: {review.admin_notes}"
        elif review.action == "rejected":
            ticket.status = "resolved"
            ticket.resolved_at = datetime.utcnow()
            ticket.resolution_notes = f"Rejected by admin. {review.admin_notes or ''}"
        elif review.action == "modified":
            ticket.status = review.new_status or "in_review"
            if review.admin_notes:
                ticket.resolution_notes = (ticket.resolution_notes or "") + f"\n\nAdmin: {review.admin_notes}"

        db.commit()
        db.refresh(ticket)
        _resolve_approval_request(db, ticket.ticket_id, current_user["id"], review.action, review.admin_notes)
        db.commit()
        return {"message": "Admin review complete", "dispute": _ticket_to_dict(ticket)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.patch("/{ticket_id}")
def update_dispute(
    ticket_id: str,
    update: DisputeUpdate,
    current_user: dict = Depends(require_role(["hr_manager", "admin"]))
):
    db = SessionLocal()
    try:
        ticket = db.query(DisputeTicket).filter(DisputeTicket.ticket_id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Dispute ticket not found")

        if update.status:
            ticket.status = update.status
            if update.status == "resolved":
                ticket.resolved_at = datetime.utcnow()
        if update.resolution_notes:
            ticket.resolution_notes = update.resolution_notes
        if update.priority:
            ticket.priority = update.priority

        db.commit()
        db.refresh(ticket)
        return {"message": "Dispute updated", "dispute": _ticket_to_dict(ticket)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def _extract_verdict(ai_response: str) -> str:
    response_lower = ai_response.lower()
    if "resolved_valid" in response_lower or "verdict: resolved_valid" in response_lower:
        return "resolved_valid"
    elif "resolved_invalid" in response_lower or "verdict: resolved_invalid" in response_lower:
        return "resolved_invalid"
    elif "escalated" in response_lower or "verdict: escalated" in response_lower:
        return "escalated"
    elif "valid" in response_lower and "discrepancy" in response_lower:
        return "resolved_valid"
    elif "correct" in response_lower and "no discrepancy" in response_lower:
        return "resolved_invalid"
    else:
        return "escalated"


def _ticket_to_dict(t: DisputeTicket) -> dict:
    return {
        "id": t.id,
        "ticket_id": t.ticket_id,
        "employee_id": t.employee_id,
        "category": t.category,
        "description": t.description,
        "expected_amount": t.expected_amount,
        "actual_amount": t.actual_amount,
        "discrepancy_amount": t.discrepancy_amount,
        "status": t.status,
        "priority": t.priority,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
        "resolution_notes": t.resolution_notes,
        "ai_reviewed": t.ai_reviewed,
        "ai_verdict": t.ai_verdict,
        "ai_analysis": t.ai_analysis,
        "ai_reviewed_at": t.ai_reviewed_at.isoformat() if t.ai_reviewed_at else None,
        "admin_reviewed": t.admin_reviewed,
        "admin_action": t.admin_action,
        "admin_notes": t.admin_notes,
        "admin_reviewed_at": t.admin_reviewed_at.isoformat() if t.admin_reviewed_at else None,
    }


def _extract_month_from_text(text: str) -> str:
    if not text:
        return None
    match = re.search(r"(20\d{2}-\d{2})", text)
    if match:
        return match.group(1)
    month_map = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12",
    }
    lower = text.lower()
    for name, mm in month_map.items():
        if name in lower:
            year_match = re.search(r"(20\d{2})", lower)
            year = year_match.group(1) if year_match else str(datetime.utcnow().year)
            return f"{year}-{mm}"
    return None


def _heuristic_risk(ticket: DisputeTicket, critic: dict) -> float:
    discrepancy_abs = abs(float(ticket.discrepancy_amount or 0))
    score = 0.2
    if discrepancy_abs >= REQUIRE_ADMIN_APPROVAL_ABOVE:
        score += 0.4
    if ticket.priority in ("high", "critical"):
        score += 0.2
    if critic.get("success") and not critic.get("is_consistent"):
        score += 0.3
    if ticket.category in ("salary", "tds", "pf"):
        score += 0.1
    return max(0.0, min(1.0, score))


def _create_or_refresh_approval_request(db, ticket: DisputeTicket, risk_score: float, proposed_action: str, reason: str):
    req = db.query(HumanApprovalRequest).filter(
        HumanApprovalRequest.request_type == "dispute_resolution",
        HumanApprovalRequest.reference_id == ticket.ticket_id,
        HumanApprovalRequest.status == "pending",
    ).first()
    if req:
        req.risk_score = risk_score
        req.proposed_action = proposed_action
        req.reason = reason
        return req
    req = HumanApprovalRequest(
        request_type="dispute_resolution",
        reference_id=ticket.ticket_id,
        employee_id=ticket.employee_id,
        risk_score=risk_score,
        proposed_action=proposed_action,
        reason=reason,
        status="pending",
    )
    db.add(req)
    return req


def _resolve_approval_request(db, ticket_id: str, reviewer_id: int, action: str, notes: str = None):
    req = db.query(HumanApprovalRequest).filter(
        HumanApprovalRequest.request_type == "dispute_resolution",
        HumanApprovalRequest.reference_id == ticket_id,
        HumanApprovalRequest.status == "pending",
    ).first()
    if not req:
        return
    req.status = "approved" if action == "approved" else "rejected"
    req.reviewed_by = reviewer_id
    req.reviewed_at = datetime.utcnow()
    req.review_notes = notes
