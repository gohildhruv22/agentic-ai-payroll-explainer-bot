"""
Tool: fetch stored agent memory for an employee.
"""
from database import SessionLocal
from models import AgentMemory


def agent_memory_fetch(employee_id: int, memory_type: str = None) -> dict:
    db = SessionLocal()
    try:
        query = db.query(AgentMemory).filter(AgentMemory.employee_id == employee_id)
        if memory_type:
            query = query.filter(AgentMemory.memory_type == memory_type)
        rows = query.order_by(AgentMemory.updated_at.desc()).all()
        return {
            "success": True,
            "memories": [
                {
                    "memory_type": m.memory_type,
                    "key": m.key,
                    "value": m.value,
                    "confidence": m.confidence,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in rows
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()

