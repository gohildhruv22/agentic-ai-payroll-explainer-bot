"""
HR dashboard aggregates: query counts, disputes, active users, intent distribution, charts data.

Restricted to hr_manager and admin roles.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from auth import require_role
from database import SessionLocal
from models import (
    AuditLog,
    DisputeTicket,
    Conversation,
    Employee,
    AutonomousJobRun,
    HumanApprovalRequest,
    AutonomousEvent,
    SlaIncident,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(current_user: dict = Depends(require_role(["hr_manager", "admin"]))):
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        total_queries_today = db.query(AuditLog).filter(
            AuditLog.timestamp >= today_start
        ).count()

        total_queries_all = db.query(AuditLog).count()

        open_disputes = db.query(DisputeTicket).filter(
            DisputeTicket.status.in_(["open", "in_review"])
        ).count()

        total_disputes = db.query(DisputeTicket).count()
        resolved_disputes = db.query(DisputeTicket).filter(
            DisputeTicket.status == "resolved"
        ).count()

        active_users = db.query(func.count(func.distinct(Conversation.employee_id))).filter(
            Conversation.timestamp >= today_start
        ).scalar() or 0

        total_employees = db.query(Employee).count()

        intent_dist = db.query(
            AuditLog.intent,
            func.count(AuditLog.id).label("count")
        ).group_by(AuditLog.intent).order_by(func.count(AuditLog.id).desc()).all()

        intent_distribution = [
            {"intent": i.intent or "general", "count": i.count}
            for i in intent_dist
        ]

        last_7_days = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = day_start + timedelta(days=1)
            count = db.query(AuditLog).filter(
                AuditLog.timestamp >= day_start,
                AuditLog.timestamp < day_end,
            ).count()
            last_7_days.append({
                "date": day.strftime("%Y-%m-%d"),
                "day": day.strftime("%a"),
                "queries": count,
            })

        recent_queries = db.query(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).limit(20).all()

        recent_list = []
        for q in recent_queries:
            emp = None
            if q.user_id:
                emp = db.query(Employee).filter(Employee.id == q.user_id).first()
            recent_list.append({
                "id": q.id,
                "employee_name": emp.name if emp else "Unknown",
                "query": q.query_text[:80] + "..." if q.query_text and len(q.query_text) > 80 else q.query_text,
                "intent": q.intent or "general",
                "agent": q.agent_used or "N/A",
                "timestamp": q.timestamp.isoformat() if q.timestamp else None,
            })

        dispute_breakdown = {
            "open": db.query(DisputeTicket).filter(DisputeTicket.status == "open").count(),
            "in_review": db.query(DisputeTicket).filter(DisputeTicket.status == "in_review").count(),
            "resolved": resolved_disputes,
            "escalated": db.query(DisputeTicket).filter(DisputeTicket.status == "escalated").count(),
        }
        autonomy_runs_today = db.query(AutonomousJobRun).filter(
            AutonomousJobRun.started_at >= today_start
        ).count()
        autonomy_failures_today = db.query(AutonomousJobRun).filter(
            AutonomousJobRun.started_at >= today_start,
            AutonomousJobRun.status == "failed",
        ).count()
        pending_approvals = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending"
        ).count()
        high_risk_pending_approvals = db.query(HumanApprovalRequest).filter(
            HumanApprovalRequest.status == "pending",
            HumanApprovalRequest.risk_score >= 0.7,
        ).count()
        approval_type_rows = db.query(
            HumanApprovalRequest.request_type,
            func.count(HumanApprovalRequest.id).label("count")
        ).filter(
            HumanApprovalRequest.status == "pending"
        ).group_by(
            HumanApprovalRequest.request_type
        ).all()
        approvals_by_type = [
            {"request_type": row.request_type, "count": row.count}
            for row in approval_type_rows
        ]
        pending_events = db.query(AutonomousEvent).filter(
            AutonomousEvent.status == "pending"
        ).count()
        failed_events_today = db.query(AutonomousEvent).filter(
            AutonomousEvent.status == "failed",
            AutonomousEvent.created_at >= today_start,
        ).count()
        open_sla_incidents = db.query(SlaIncident).filter(
            SlaIncident.status.in_(["open", "acknowledged"])
        ).count()
        critical_open_sla_incidents = db.query(SlaIncident).filter(
            SlaIncident.status.in_(["open", "acknowledged"]),
            SlaIncident.severity == "critical",
        ).count()

        return {
            "total_queries_today": total_queries_today,
            "total_queries_all": total_queries_all,
            "open_disputes": open_disputes,
            "total_disputes": total_disputes,
            "active_users_today": active_users,
            "total_employees": total_employees,
            "intent_distribution": intent_distribution,
            "query_volume_7days": last_7_days,
            "recent_queries": recent_list,
            "dispute_breakdown": dispute_breakdown,
            "autonomy": {
                "runs_today": autonomy_runs_today,
                "failures_today": autonomy_failures_today,
                "pending_approvals": pending_approvals,
                "high_risk_pending_approvals": high_risk_pending_approvals,
                "pending_approvals_by_type": approvals_by_type,
                "pending_events": pending_events,
                "failed_events_today": failed_events_today,
                "open_sla_incidents": open_sla_incidents,
                "critical_open_sla_incidents": critical_open_sla_incidents,
            },
        }
    finally:
        db.close()
