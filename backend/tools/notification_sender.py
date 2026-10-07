"""
Creates an in-app Notification row for an employee (used after disputes or status updates).
"""
import json
from datetime import datetime
from database import SessionLocal
from models import Notification


def notification_sender(
    employee_id: int,
    channel: str = "in_app",
    subject: str = "",
    body: str = ""
) -> dict:
    db = SessionLocal()
    try:
        notification = Notification(
            employee_id=employee_id,
            channel=channel,
            subject=subject,
            body=body,
            status="sent",
            sent_at=datetime.utcnow(),
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        return {
            "success": True,
            "notification_id": notification.id,
            "message": f"Notification sent via {channel}: {subject}",
            "channel": channel,
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}
    finally:
        db.close()
