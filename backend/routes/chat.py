"""
Chat API: send messages to the AI orchestrator and persist conversation history.

POST /api/chat saves the user turn, runs OrchestratorAgent (Groq + tools), saves the reply.
Also lists past sessions and loads history per session_id for the logged-in employee.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import get_current_user
from database import SessionLocal
from models import Conversation
from models import AgentMemory
from agents.orchestrator import OrchestratorAgent

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent: str
    intent: str
    tools_called: list = []
    requires_human_approval: bool = False


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    # New chat gets a fresh UUID; existing sessions reuse session_id for context
    session_id = request.session_id or str(uuid.uuid4())
    db = SessionLocal()

    try:
        history_records = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.employee_id == current_user["id"]
        ).order_by(Conversation.timestamp.asc()).all()

        conversation_history = [
            {"role": rec.role, "content": rec.message}
            for rec in history_records
        ]

        user_conv = Conversation(
            session_id=session_id,
            employee_id=current_user["id"],
            role="user",
            message=request.message,
            timestamp=datetime.utcnow(),
        )
        db.add(user_conv)
        db.commit()

        orchestrator = OrchestratorAgent()
        result = orchestrator.process_query(
            user_message=request.message,
            employee_id=current_user["id"],
            session_id=session_id,
            conversation_history=conversation_history,
        )

        response_text = result.get("response", "I'm sorry, I couldn't process your request.")
        agent_name = result.get("agent", "General Assistant")
        intent = result.get("intent", "general")
        tools = result.get("tools_called", [])
        requires_human_approval = bool(result.get("requires_human_approval", False))
        approval_reason = result.get("approval_reason", "")

        import json
        assistant_conv = Conversation(
            session_id=session_id,
            employee_id=current_user["id"],
            role="assistant",
            message=response_text,
            timestamp=datetime.utcnow(),
            metadata_json=json.dumps({
                "agent": agent_name,
                "intent": intent,
                "requires_human_approval": requires_human_approval,
                "approval_reason": approval_reason,
            }),
        )
        db.add(assistant_conv)

        _capture_user_memory(db, current_user["id"], request.message)
        db.commit()

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            agent=agent_name,
            intent=intent,
            tools_called=tools,
            requires_human_approval=requires_human_approval,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
    finally:
        db.close()


def _capture_user_memory(db, employee_id: int, message: str):
    text = (message or "").lower()
    pref_val = None
    if "new regime" in text and ("switch" in text or "prefer" in text or "choose" in text):
        pref_val = "new"
    elif "old regime" in text and ("switch" in text or "prefer" in text or "choose" in text):
        pref_val = "old"
    if not pref_val:
        return

    mem = db.query(AgentMemory).filter(
        AgentMemory.employee_id == employee_id,
        AgentMemory.memory_type == "preference",
        AgentMemory.key == "tax_regime_preference",
    ).first()
    if mem:
        mem.value = pref_val
        mem.confidence = min(1.0, float(mem.confidence or 0.5) + 0.1)
    else:
        mem = AgentMemory(
            employee_id=employee_id,
            memory_type="preference",
            key="tax_regime_preference",
            value=pref_val,
            confidence=0.7,
        )
        db.add(mem)


@router.get("/history/{session_id}")
def get_chat_history(session_id: str, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.employee_id == current_user["id"],
        ).order_by(Conversation.timestamp.asc()).all()

        return {
            "session_id": session_id,
            "messages": [
                {
                    "id": rec.id,
                    "role": rec.role,
                    "message": rec.message,
                    "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
                    "metadata": rec.metadata_json,
                }
                for rec in records
            ]
        }
    finally:
        db.close()


@router.get("/sessions")
def get_sessions(current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        from sqlalchemy import func, distinct
        sessions = db.query(
            Conversation.session_id,
            func.min(Conversation.message).label("first_message"),
            func.min(Conversation.timestamp).label("created_at"),
            func.max(Conversation.timestamp).label("last_active"),
            func.count(Conversation.id).label("message_count"),
        ).filter(
            Conversation.employee_id == current_user["id"],
            Conversation.role == "user",
        ).group_by(
            Conversation.session_id
        ).order_by(
            func.max(Conversation.timestamp).desc()
        ).all()

        return {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "title": s.first_message[:50] + "..." if len(s.first_message) > 50 else s.first_message,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "last_active": s.last_active.isoformat() if s.last_active else None,
                    "message_count": s.message_count,
                }
                for s in sessions
            ]
        }
    finally:
        db.close()
