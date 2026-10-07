"""
HR policy documents API: list, fetch by id, and (HR/admin) upload policy text.

Policies are stored as rows in PolicyDocument; the UI can browse full text for employees.
"""
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user, require_role
from database import SessionLocal
from models import PolicyDocument
from datetime import datetime

router = APIRouter(prefix="/api/policies", tags=["Policies"])


@router.get("")
def list_policies(current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        policies = db.query(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).all()
        return {
            "policies": [
                {
                    "id": p.id,
                    "title": p.title,
                    "category": p.category,
                    "content": p.content,
                    "source_file": p.source_file,
                    "uploaded_at": p.uploaded_at.isoformat() if p.uploaded_at else None,
                }
                for p in policies
            ]
        }
    finally:
        db.close()


@router.get("/{policy_id}")
def get_policy(policy_id: int, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        policy = db.query(PolicyDocument).filter(PolicyDocument.id == policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return {
            "policy": {
                "id": policy.id,
                "title": policy.title,
                "category": policy.category,
                "content": policy.content,
                "source_file": policy.source_file,
                "uploaded_at": policy.uploaded_at.isoformat() if policy.uploaded_at else None,
            }
        }
    finally:
        db.close()


@router.post("/upload")
def upload_policy(
    title: str,
    category: str,
    content: str,
    current_user: dict = Depends(require_role(["hr_manager", "admin"]))
):
    db = SessionLocal()
    try:
        policy = PolicyDocument(
            title=title,
            category=category,
            content=content,
            source_file=f"{title.lower().replace(' ', '_')}.pdf",
            uploaded_at=datetime.utcnow(),
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return {
            "message": "Policy uploaded successfully",
            "policy_id": policy.id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
