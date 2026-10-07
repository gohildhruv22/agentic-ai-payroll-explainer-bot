"""
Notification APIs for authenticated users.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import SessionLocal
from models import Notification

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/my")
def get_my_notifications(current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.query(Notification).filter(
            Notification.employee_id == current_user["id"]
        ).order_by(Notification.sent_at.desc()).limit(100).all()
        unread_count = sum(1 for n in rows if (n.status or "").lower() != "read")
        return {
            "unread_count": unread_count,
            "notifications": [
                {
                    "id": n.id,
                    "channel": n.channel,
                    "subject": n.subject,
                    "body": n.body,
                    "status": n.status,
                    "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                }
                for n in rows
            ],
        }
    finally:
        db.close()


@router.post("/mark-read/{notification_id}")
def mark_notification_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        row = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.employee_id == current_user["id"],
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Notification not found")
        row.status = "read"
        db.commit()
        return {"success": True, "notification_id": notification_id, "status": "read"}
    finally:
        db.close()


@router.post("/mark-all-read")
def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.query(Notification).filter(
            Notification.employee_id == current_user["id"],
            Notification.status != "read",
        ).all()
        for row in rows:
            row.status = "read"
        db.commit()
        return {"success": True, "updated": len(rows)}
    finally:
        db.close()

