"""
Admin audit log API: paginated list of AI query / agent activity from AuditLog.

Used for compliance review; admin-only.
"""
from fastapi import APIRouter, Depends
from auth import require_role
from database import SessionLocal
from models import AuditLog, Employee

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/logs")
def get_audit_logs(
    page: int = 1,
    per_page: int = 50,
    current_user: dict = Depends(require_role(["admin"]))
):
    db = SessionLocal()
    try:
        total = db.query(AuditLog).count()
        offset = (page - 1) * per_page

        logs = db.query(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).offset(offset).limit(per_page).all()

        result = []
        for log in logs:
            emp = None
            if log.user_id:
                emp = db.query(Employee).filter(Employee.id == log.user_id).first()
            result.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "user_id": log.user_id,
                "employee_name": emp.name if emp else "System",
                "query_text": log.query_text,
                "intent": log.intent,
                "agent_used": log.agent_used,
                "tools_called": log.tools_called_json,
                "response_summary": log.response_summary,
                "escalation_triggered": log.escalation_triggered,
            })

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "logs": result,
        }
    finally:
        db.close()
