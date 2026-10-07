# Agentic AI Payroll Explainer Bot

AI-powered multi-agent payroll assistant for Employees. Built with FastAPI, React, and Groq (Llama 3.3 70B).
![Agentic AI Payroll Explainer Bot Banner](Banner.png)

## Architecture

- **Orchestrator** — Keyword-based intent scoring, then routes to one specialist (see `agents/agentic/registry.py`)
- **Payroll Calculator** — Salary breakdowns, CTC computation, payslip generation
- **Compliance Agent** — Indian tax law, PF/ESIC, TDS calculations, web search for latest updates
- **Policy Explainer** — RAG-based answers from HR policy documents
- **Dispute Resolver** — Payslip discrepancy handling, ticket creation, escalation
- **General Assistant** — Fallback when intent is `general`
![Agentic AI Payroll Explainer Bot Architecure](Architecture.png)


### AI agent framework (LangChain + LangGraph)

All chat specialists share the same **agentic** stack:

- **LangChain** — `langchain-groq` (`ChatGroq`) and `StructuredTool` definitions built from your existing tool metadata + Python functions
- **LangGraph** — `create_react_agent` (ReAct-style graph: model ↔ tools until a final answer), with recursion limits aligned to `MAX_AGENT_ITERATIONS` in `config.py`
- **Shared module** — `backend/agents/agentic/` (`groq_llm.py`, `tools_builder.py`, `react_runner.py`, `registry.py`); **`BaseAgent`** (`agents/base_agent.py`) invokes this graph so every specialist behaves consistently

Orchestration (who answers) stays in Python; **tool execution** is handled inside the LangGraph agent loop. On Groq rate limits, the stack retries with the configured fallback model (`GROQ_FALLBACK_MODEL`).

## Prerequisites

- Python 3.10+
- Node.js 18+
- Groq API key ([console.groq.com](https://console.groq.com))

## Quick Start

### 1. Backend Setup


```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add your GROQ_API_KEY (optional: APP_PORT defaults to 8001)
python seed_data.py
uvicorn main:app --reload --port 8001
# Or: python main.py   (uses APP_PORT from .env, default 8001)
```

The API listens on **http://127.0.0.1:8001** by default. The Vite dev server proxies browser requests from `/api` to that URL (see `frontend/vite.config.js`; override with `VITE_DEV_API_PROXY` in `frontend/.env` if needed).

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Employee | rahul.sharma@company.com | password123 |
| HR Manager | priya.patel@company.com | password123 |
| Admin | neha.agarwal@company.com | password123 |

## API Keys

| Key | Required | Purpose |
|-----|----------|---------|
| `GROQ_API_KEY` | **Yes** | AI model (Llama 3.3 70B) |
| `SERPAPI_KEY` | Optional | Web search for tax/law updates |
| `NEWS_API_KEY` | Optional | News search for compliance |

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts
- **AI**: Groq-hosted models via **LangChain** (`langchain-groq`, `langchain-core`) and **LangGraph** (`create_react_agent` ReAct graphs); see `backend/requirements.txt` for pins
- **Auth**: JWT + bcrypt
- **PDF**: ReportLab for payslip generation

## Features

- Multi-agent AI chat with **LangGraph** ReAct-style tool calling (shared `BaseAgent` + specialist registry)
- Salary breakdown with PDF payslip download
- Old vs New tax regime comparison (FY 2025-26)
- RAG-based policy search
- Dispute ticket system with escalation
- HR dashboard with analytics
- Role-based access control
- Full audit trail
