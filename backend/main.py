"""
Payroll Bot API entry point (FastAPI application).

Wires up CORS, request logging, rate limiting, database init on startup, JWT login,
and all feature routers (chat, payroll, disputes, etc.). Run with uvicorn or `python main.py`.
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import APP_PORT, CORS_ORIGINS
from database import init_db, SessionLocal
from middleware import RateLimitMiddleware, RequestLoggingMiddleware
from models import Employee
from auth import verify_password, create_access_token, get_current_user, hash_password

from routes.chat import router as chat_router
from routes.employees import router as employees_router
from routes.payroll import router as payroll_router
from routes.disputes import router as disputes_router
from routes.dashboard import router as dashboard_router
from routes.policies import router as policies_router
from routes.audit import router as audit_router
from routes.autonomy import router as autonomy_router
from routes.notifications import router as notifications_router
from autonomy_engine import AutonomyEngine
import runtime_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("payroll_bot")
autonomy_engine = AutonomyEngine()
runtime_state.autonomy_engine = autonomy_engine

# FastAPI app: all routes live here or on included routers under /api/...
app = FastAPI(
    title="Payroll Explainer Bot API",
    description="Agentic AI Payroll Explainer Bot for HR Department",
    version="1.0.0",
)

# Browser clients (Vite on :5173) may call this API; CORS allows those origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


class LoginRequest(BaseModel):
    email: str
    password: str


@app.on_event("startup")
def startup():
    init_db()
    autonomy_engine.start()
    logger.info("Payroll Explainer Bot API started")


@app.on_event("shutdown")
def shutdown():
    autonomy_engine.stop()


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Payroll Explainer Bot"}


@app.post("/api/auth/login")
def login(request: LoginRequest):
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.email == request.email).first()
        if not employee:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(request.password, employee.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token({
            "employee_id": employee.id,
            "email": employee.email,
            "role": employee.role,
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": employee.id,
                "emp_id": employee.emp_id,
                "name": employee.name,
                "email": employee.email,
                "department": employee.department,
                "designation": employee.designation,
                "role": employee.role,
            }
        }
    finally:
        db.close()


@app.get("/api/auth/me")
def get_me(current_user: dict = __import__("fastapi").Depends(get_current_user)):
    return {"user": current_user}


app.include_router(chat_router)
app.include_router(employees_router)
app.include_router(payroll_router)
app.include_router(disputes_router)
app.include_router(dashboard_router)
app.include_router(policies_router)
app.include_router(audit_router)
app.include_router(autonomy_router)
app.include_router(notifications_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=APP_PORT, reload=True)
