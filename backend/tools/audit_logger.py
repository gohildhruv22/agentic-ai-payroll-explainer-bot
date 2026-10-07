"""
Tool: append a row to AuditLog (who asked what, which agent, tools, short summary).
"""
import json
from datetime import datetime
from database import SessionLocal
from models import AuditLog


def audit_logger(
    user_id: int = None,
    query_text: str = "",
    intent: str = "",
    agent_used: str = "",
    tools_called: list = None,
    response_summary: str = "",
    escalation_triggered: bool = False,
) -> dict:
    db = SessionLocal()
    try:
        log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            query_text=query_text[:500] if query_text else "",
            intent=intent,
            agent_used=agent_used,
            tools_called_json=json.dumps(tools_called or []),
            response_summary=response_summary[:500] if response_summary else "",
            escalation_triggered=escalation_triggered,
        )
        db.add(log)
        db.commit()
        return {"success": True, "log_id": log.id}
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}
    finally:
        db.close()
