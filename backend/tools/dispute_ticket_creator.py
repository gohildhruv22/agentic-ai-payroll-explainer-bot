"""
Tool: insert a new DisputeTicket with generated ticket_id and optional evidence JSON.
"""
import json
import random
import string
from datetime import datetime
from database import SessionLocal
from models import DisputeTicket


def dispute_ticket_creator(
    employee_id: int,
    category: str,
    description: str,
    expected_amount: float = None,
    actual_amount: float = None,
    evidence: dict = None,
    priority: str = "medium",
) -> dict:
    db = SessionLocal()
    try:
        ticket_id = _generate_ticket_id(db)
        discrepancy = None
        if expected_amount is not None and actual_amount is not None:
            discrepancy = round(expected_amount - actual_amount, 2)

        ticket = DisputeTicket(
            ticket_id=ticket_id,
            employee_id=employee_id,
            category=category,
            description=description,
            expected_amount=expected_amount,
            actual_amount=actual_amount,
            discrepancy_amount=discrepancy,
            evidence_json=json.dumps(evidence) if evidence else None,
            status="open",
            priority=priority,
            created_at=datetime.utcnow(),
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return {
            "success": True,
            "ticket_id": ticket.ticket_id,
            "status": "open",
            "priority": priority,
            "message": f"Dispute ticket {ticket.ticket_id} created successfully. Our HR team will review it within 48 hours.",
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}
    finally:
        db.close()


def _generate_ticket_id(db) -> str:
    while True:
        random_part = ''.join(random.choices(string.digits, k=4))
        ticket_id = f"DSP-{random_part}"
        existing = db.query(DisputeTicket).filter(DisputeTicket.ticket_id == ticket_id).first()
        if not existing:
            return ticket_id
