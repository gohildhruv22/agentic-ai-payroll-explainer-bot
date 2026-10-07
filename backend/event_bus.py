"""
Database-backed lightweight event bus for autonomy workflows.
"""
import json
from datetime import datetime

from database import SessionLocal
from models import AutonomousEvent


def publish_event(event_type: str, payload: dict | None = None) -> dict:
    db = SessionLocal()
    try:
        row = AutonomousEvent(
            event_type=event_type,
            payload_json=json.dumps(payload or {}),
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"success": True, "event_id": row.id}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def pull_pending_events(limit: int = 20) -> list[AutonomousEvent]:
    db = SessionLocal()
    try:
        rows = db.query(AutonomousEvent).filter(
            AutonomousEvent.status == "pending"
        ).order_by(AutonomousEvent.created_at.asc()).limit(limit).all()
        # Detach ids/data for external processing; keep function simple.
        return [
            {
                "id": r.id,
                "event_type": r.event_type,
                "payload": json.loads(r.payload_json or "{}"),
            }
            for r in rows
        ]
    finally:
        db.close()


def mark_event_processed(event_id: int):
    db = SessionLocal()
    try:
        row = db.query(AutonomousEvent).filter(AutonomousEvent.id == event_id).first()
        if row:
            row.status = "processed"
            row.processed_at = datetime.utcnow()
            row.error = None
            db.commit()
    finally:
        db.close()


def mark_event_failed(event_id: int, error: str):
    db = SessionLocal()
    try:
        row = db.query(AutonomousEvent).filter(AutonomousEvent.id == event_id).first()
        if row:
            row.status = "failed"
            row.processed_at = datetime.utcnow()
            row.error = str(error)[:1000]
            db.commit()
    finally:
        db.close()

