"""
Central configuration loaded from environment variables (.env).

Holds API keys (Groq, search), JWT settings, database URL, CORS, server port, and AI tuning
constants. Other modules import these values instead of reading os.environ directly.
"""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")

JWT_SECRET = os.getenv("JWT_SECRET", "default-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./payroll_bot.db")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

APP_ENV = os.getenv("APP_ENV", "development")
APP_PORT = int(os.getenv("APP_PORT", "8001"))

MAX_AGENT_ITERATIONS = 10
RATE_LIMIT_PER_MINUTE = 100

# Autonomous engine configuration
AUTONOMY_ENABLED = os.getenv("AUTONOMY_ENABLED", "true").lower() == "true"
AUTONOMY_POLL_SECONDS = int(os.getenv("AUTONOMY_POLL_SECONDS", "45"))
AUTONOMY_DISPUTE_REVIEW_MINUTES = int(os.getenv("AUTONOMY_DISPUTE_REVIEW_MINUTES", "5"))
AUTONOMY_PAYROLL_AUDIT_MINUTES = int(os.getenv("AUTONOMY_PAYROLL_AUDIT_MINUTES", "30"))
AUTONOMY_TAX_ADVISOR_MINUTES = int(os.getenv("AUTONOMY_TAX_ADVISOR_MINUTES", "720"))

# Phase 2: planner-executor-critic and human approval thresholds
PEC_ENABLED = os.getenv("PEC_ENABLED", "true").lower() == "true"
AUTO_APPROVAL_MAX_DISCREPANCY = float(os.getenv("AUTO_APPROVAL_MAX_DISCREPANCY", "2000"))
REQUIRE_ADMIN_APPROVAL_ABOVE = float(os.getenv("REQUIRE_ADMIN_APPROVAL_ABOVE", "5000"))

# Phase 3: event bus + self-healing + SLA policies
AUTONOMY_JOB_MAX_RETRIES = int(os.getenv("AUTONOMY_JOB_MAX_RETRIES", "2"))
AUTONOMY_JOB_FAILURE_COOLDOWN_SECONDS = int(os.getenv("AUTONOMY_JOB_FAILURE_COOLDOWN_SECONDS", "180"))
AUTONOMY_JOB_FAILURE_STREAK_THRESHOLD = int(os.getenv("AUTONOMY_JOB_FAILURE_STREAK_THRESHOLD", "3"))
SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT = int(os.getenv("SLA_PENDING_APPROVAL_HIGH_RISK_LIMIT", "15"))
SLA_FAILED_JOBS_DAILY_LIMIT = int(os.getenv("SLA_FAILED_JOBS_DAILY_LIMIT", "10"))
