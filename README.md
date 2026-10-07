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


---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Objectives](#2-project-objectives)
3. [System Architecture](#3-system-architecture)
4. [Agent Design & Capabilities](#4-agent-design--capabilities)
5. [Tool Ecosystem](#5-tool-ecosystem)
6. [Agentic Workflows](#6-agentic-workflows)
7. [Technology Stack](#7-technology-stack)
8. [Database Schema](#8-database-schema)
9. [API Endpoints](#9-api-endpoints)
10. [Frontend Design](#10-frontend-design)
11. [Security & Compliance](#11-security--compliance)
12. [Dispute Review System](#12-dispute-review-system)
13. [Project Metrics](#13-project-metrics)
14. [Deployment Guide](#14-deployment-guide)
15. [Default Credentials](#15-default-credentials)

---

## 1. Executive Summary

The Agentic AI Payroll Explainer Bot is a production-ready, multi-agent AI system built for the Human Resources department. It enables employees and HR managers to get instant, accurate, policy-grounded answers to all payroll-related queries — salary breakdowns, tax calculations, leave balances, compliance questions, and dispute resolution.

Unlike a simple chatbot, this system is a **true agentic AI** — it autonomously plans, reasons, calls tools, queries databases, performs calculations, and completes multi-step workflows without human intervention. It is powered by **Groq's Llama 3.3 70B** (via **LangChain `ChatGroq`**) and **LangGraph**'s **`create_react_agent`** pattern: a compiled ReAct graph that alternates between the language model and tool execution until a final answer. **Intent routing** uses keyword scoring plus a central **specialist registry** (`agents/agentic/registry.py`); each specialist is still a `BaseAgent` instance sharing the same LangChain/LangGraph stack.

### Key Highlights

- **6 AI Agents**: Orchestrator + 5 specialized sub-agents
- **10 Custom Tools**: Database queries, tax calculators, RAG search, PDF generation, web search
- **18 Demo Employees** with 108 salary records across 6 months
- **5 HR Policy Documents** with keyword-based RAG search
- **AI-Powered Dispute Review**: Automatic analysis with admin oversight
- **Role-Based Access Control**: Employee, HR Manager, and Admin roles
- **Professional Enterprise UI**: React 18 + Tailwind CSS

---

## 2. Project Objectives

| # | Objective | Status |
|---|---|---|
| 1 | Reduce HR payroll query resolution time from hours to seconds | ✅ Achieved |
| 2 | Provide 24/7 availability for payroll questions | ✅ Achieved |
| 3 | Ensure accurate, policy-grounded, legally compliant answers | ✅ Achieved |
| 4 | Give employees self-service access to payslips and tax data | ✅ Achieved |
| 5 | Automate multi-step payroll workflows | ✅ Achieved |
| 6 | Maintain complete audit trail for compliance | ✅ Achieved |
| 7 | Support role-based access control | ✅ Achieved |
| 8 | AI-powered dispute resolution with admin review | ✅ Achieved |

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (React 18)               │
│  Login │ Chat │ Payroll │ Disputes │ Dashboard │ ...│
└──────────────────────┬──────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────┐
│                  BACKEND (FastAPI)                  │
│  ┌─────────────────────────────────────────────┐    │
│  │           ORCHESTRATOR                         │  │
│  │   Intent (keywords) → Registry → Specialist │  │
│  └──────┬──────┬──────┬──────┬──────┬───────────┘   │
│         │      │      │      │      │               │
│  ┌──────▼┐ ┌──▼───┐ ┌▼────┐ ┌▼────┐ ┌▼──────┐       │
│  │Payroll│ │Compli│ │Polic│ │Dispu│ │Dispute│       │
│  │ Calc  │ │ance  │ │y Exp│ │te   │ │Review │       │
│  │ Agent │ │Agent │ │Agent│ │Resol│ │Agent  │       │
│  └──┬────┘ └──┬───┘ └─┬───┘ └─┬───┘ └──┬────┘       │
│     │         │       │       │        │            │
│  ┌──▼─────────▼───────▼───────▼────────▼─────┐      │
│  │              TOOL LAYER (10 Tools)          │    │
│  │ payroll_db │ tax_calc │ rag │ pdf │ web... │     │
│  └──────────────────┬─────────────────────────┘     │
│                     │                               │
│  ┌──────────────────▼─────────────────────────┐     │
│  │           DATA LAYER (SQLite)               │    │
│  │ Employees │ Salary │ Leave │ Disputes │ ... │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 3.2 Architecture Layers

| Layer | Component | Technology | Purpose |
|-------|-----------|------------|---------|
| Layer 1 | User Interface | React 18, Tailwind CSS, Recharts | Chat UI, dashboards, forms |
| Layer 2 | API Gateway | FastAPI, JWT Auth | REST endpoints, CORS, rate limiting |
| Layer 3 | Orchestrator | Keyword intent + `agents/agentic/registry.py` | Map intent → specialist factory; enrich message with employee context |
| Layer 4 | Agent runtime | LangChain `ChatGroq` + LangGraph `create_react_agent` | ReAct graph: model ↔ tools until final message; shared by all `BaseAgent` specialists |
| Layer 5 | Tools | LangChain `StructuredTool` + Python callables | Same tool functions; exposed to the graph via structured tools |
| Layer 6 | Data Store | SQLite + SQLAlchemy ORM | Persistent storage |

### 3.3 LangChain, LangGraph, and the `agentic` package

The **tool-calling loop** is implemented with the standard LangChain/LangGraph agentic pattern (not a hand-rolled HTTP loop):

| Piece | Role |
|-------|------|
| **`langchain-groq`** | `ChatGroq` — Groq-hosted models (`GROQ_MODEL` / `GROQ_FALLBACK_MODEL` from `.env`) |
| **`langchain-core`** | Message types (`SystemMessage` / `HumanMessage` / `AIMessage` / `ToolMessage`), `StructuredTool` |
| **`langgraph.prebuilt.create_react_agent`** | Builds a **ReAct** graph: **agent** node (LLM) → **tools** node → repeat until the model returns a final answer without pending tool calls |
| **`agents/agentic/groq_llm.py`** | Shared `make_chat_groq()` factory |
| **`agents/agentic/tools_builder.py`** | Maps existing OpenAI-style tool JSON + Python callables → `StructuredTool` list |
| **`agents/agentic/react_runner.py`** | `run_react_specialist()` — runs the compiled graph, sets `recursion_limit` from `MAX_AGENT_ITERATIONS`, collects `tools_called` and final text |
| **`agents/agentic/registry.py`** | Intent → `(display name, create_*_agent factory)` for Payroll, Compliance, Policy, Dispute |
| **`agents/base_agent.py`** | All specialists instantiate `BaseAgent`; `run()` calls `run_react_specialist()` so behaviour is consistent |

**Rate limits:** On Groq **429** / rate-limit errors, the runner retries once using the **fallback** model (same graph, smaller/faster model).

**Dispute Review** and other non-chat agents that use `BaseAgent` follow the same LangGraph path when invoked from API routes.

---

## 4. Agent Design & Capabilities

### 4.1 Orchestrator Agent

The central brain of the system. Every user query flows through the Orchestrator.

**Responsibilities:**
- Intent classification using keyword scoring across 5 categories (plus **general** → General Assistant)
- Employee profile enrichment (CTC, location, tax regime injected into context)
- Delegation via **`get_specialist_factory(intent)`** in `agents/agentic/registry.py` to the appropriate sub-agent factory (or inline **General Assistant** when no specialist matches)
- Response synthesis and formatting (specialist returns final natural-language answer)
- Audit logging of every interaction

**Intent Categories:**
| Intent | Keywords (sample) | Routed To |
|--------|-------------------|-----------|
| salary | salary, take-home, CTC, payslip, deduction | Payroll Calculator |
| tax | TDS, income tax, old/new regime, 80C, ITR | Compliance Agent |
| compliance | PF, ESIC, gratuity, labour law, statutory | Compliance Agent |
| policy | leave, encashment, notice period, POSH | Policy Explainer |
| dispute | wrong, incorrect, discrepancy, complaint | Dispute Resolver |
| general | anything else | General Assistant |

### 4.2 Payroll Calculator Agent

**Capabilities:**
- Gross salary computation from CTC structure
- PF, ESIC, Professional Tax deduction breakdown
- HRA exemption calculation (city-tier + rent-based)
- Overtime, arrears, and bonus handling
- Old vs New tax regime comparison with recommendation
- Month-over-month salary change explanation
- PDF payslip generation and download

**Tools Used:** `payroll_db_fetch`, `tax_calculator`, `leave_attendance_fetch`, `payslip_generator`

### 4.3 Compliance Agent

**Capabilities:**
- TDS calculation under FY 2025-26 slabs (both regimes)
- PF and ESIC compliance verification
- Gratuity eligibility and computation
- Form 16, Form 26AS, ITR filing guidance
- Real-time web search for budget/law updates (via SERP API)

**Tools Used:** `tax_calculator`, `policy_search_rag`, `web_search`

### 4.4 Policy Explainer Agent

**Capabilities:**
- RAG-based search over 5 HR policy documents
- Leave policy: types, accrual, encashment, carry-forward
- Variable pay and appraisal cycle details
- Reimbursement policies
- POSH, code of conduct, grievance procedures

**Tools Used:** `policy_search_rag`, `leave_attendance_fetch`

### 4.5 Dispute Resolver Agent

**Capabilities:**
- Validates employee claims against actual payroll data
- Re-runs salary calculations to verify disputed amounts
- Creates formal dispute tickets with ticket IDs
- Sends notifications to employee and HR
- Escalates high-value discrepancies

**Tools Used:** `payroll_db_fetch`, `tax_calculator`, `policy_search_rag`, `dispute_ticket_creator`, `notification_sender`

### 4.6 Dispute Review Agent (NEW in v2)

**Capabilities:**
- Automatically reviews open dispute tickets
- Fetches payroll data and independently recalculates
- Issues verdicts: `resolved_valid`, `resolved_invalid`, or `escalated`
- Auto-escalates discrepancies > ₹20,000
- Provides structured analysis for admin review

**Tools Used:** `payroll_db_fetch`, `tax_calculator`, `policy_search_rag`, `leave_attendance_fetch`

---

## 5. Tool Ecosystem

| Tool | Function | Used By |
|------|----------|---------|
| `payroll_db_fetch` | Retrieve salary records from database | Payroll Calculator, Dispute Resolver, Dispute Review |
| `tax_calculator` | Compute TDS, PF, ESIC, HRA exemption, gratuity | Payroll Calculator, Compliance, Dispute Resolver |
| `policy_search_rag` | Keyword-based search over HR policy documents | Policy Explainer, Compliance, Dispute Resolver |
| `payslip_generator` | Generate PDF payslip using ReportLab | Payroll Calculator |
| `leave_attendance_fetch` | Retrieve leave balance and attendance data | Payroll Calculator, Policy Explainer, Dispute Review |
| `web_search` | SERP API + News API for real-time updates | Compliance Agent |
| `notification_sender` | Log notifications to database | Dispute Resolver |
| `audit_logger` | Record every agent action for compliance | Orchestrator |
| `dispute_ticket_creator` | Create dispute tickets with auto-generated IDs | Dispute Resolver |
| `employee_profile_fetch` | Retrieve employee master data | Orchestrator, All Agents |

### Tax Calculator Details (FY 2025-26)

**New Regime Slabs:**
| Income Range | Rate |
|---|---|
| ₹0 – ₹4,00,000 | 0% |
| ₹4,00,001 – ₹8,00,000 | 5% |
| ₹8,00,001 – ₹12,00,000 | 10% |
| ₹12,00,001 – ₹16,00,000 | 15% |
| ₹16,00,001 – ₹20,00,000 | 20% |
| ₹20,00,001 – ₹24,00,000 | 25% |
| Above ₹24,00,000 | 30% |
| Standard Deduction | ₹75,000 |
| Rebate u/s 87A | Up to ₹12L taxable income |

**Old Regime Slabs:**
| Income Range | Rate |
|---|---|
| ₹0 – ₹2,50,000 | 0% |
| ₹2,50,001 – ₹5,00,000 | 5% |
| ₹5,00,001 – ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |
| Standard Deduction | ₹50,000 |
| HRA, 80C (₹1.5L), 80D allowed | |

**Health & Education Cess:** 4% on total tax

---

## 6. Agentic Workflows

At execution time, each step below runs inside the **LangGraph ReAct** graph for that specialist: the model may issue one or more tool calls per “round,” tools execute, and results are fed back until the model produces the user-facing answer.

### Workflow 1: Salary Breakdown Query
```
User: "What is my take-home salary this month?"
  → Orchestrator: classify intent = "salary"
  → Payroll Calculator Agent activated
  → Tool: payroll_db_fetch(employee_id, "2026-04")
  → Tool: leave_attendance_fetch(employee_id, "2026-04")
  → Agent: computes breakdown, formats table
  → Orchestrator: returns structured response with salary table
  → Audit Logger: logs interaction
```

### Workflow 2: Tax Regime Comparison
```
User: "Should I choose old or new tax regime?"
  → Orchestrator: classify intent = "tax"
  → Compliance Agent activated
  → Tool: tax_calculator(annual_gross, regime="both", hra, rent, city)
  → Agent: compares both regimes, calculates savings
  → Returns comparison table with recommendation
```

### Workflow 3: Dispute Resolution
```
User: "My HRA deduction seems wrong this month"
  → Orchestrator: classify intent = "dispute"
  → Dispute Resolver Agent activated
  → Tool: payroll_db_fetch (current + previous month)
  → Tool: tax_calculator (verify HRA exemption)
  → Tool: policy_search_rag ("HRA policy")
  → Agent: compares expected vs actual
  → Tool: dispute_ticket_creator (if discrepancy found)
  → Tool: notification_sender (alert HR)
  → Returns ticket ID + explanation
```

### Workflow 4: AI Dispute Review (Admin)
```
Admin: clicks "AI Review" on dispute DSP-0001
  → Dispute Review Agent activated
  → Tool: payroll_db_fetch (employee salary data)
  → Tool: tax_calculator (independent verification)
  → Tool: policy_search_rag (company rules)
  → Agent: analyzes and issues verdict
  → Verdict saved to database
  → Admin reviews and approves/rejects/modifies
```

---

## 7. Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| AI Model | Groq (Llama 3.3 70B) via LangChain `ChatGroq` | Latest | Core reasoning engine |
| Agent graph | LangGraph `create_react_agent` | 0.2.x–0.4.x (see `requirements.txt`) | ReAct tool-calling loop |
| LangChain core | `langchain-core` | 1.2.8+ (see `requirements.txt`) | Messages, tools, runnables |
| LangChain Groq | `langchain-groq` | 1.x (see `requirements.txt`) | Groq chat model integration |
| Fallback Model | Groq (Llama 3.1 8B Instant) | Latest | Rate limit fallback (same stack) |
| Backend Framework | FastAPI | 0.115.0 | REST API |
| ORM | SQLAlchemy | 2.0.32 | Database abstraction |
| Database | SQLite | Built-in | Data storage |
| Authentication | python-jose + bcrypt | JWT | Token-based auth |
| PDF Generation | ReportLab | 4.2.2 | Payslip PDFs |
| Frontend Framework | React | 18.3.1 | UI components |
| Build Tool | Vite | 5.3.3 | Frontend bundling |
| CSS | Tailwind CSS | 3.4.4 | Styling |
| Charts | Recharts | 2.12.7 | Dashboard charts |
| HTTP Client | Axios | 1.7.2 | API calls |
| Notifications | react-hot-toast | 2.4.1 | Toast messages |
| Markdown | react-markdown | 9.0.1 | Chat rendering |
| Icons | Lucide React | 0.400.0 | UI icons |
| Web Search | SERP API + News API | — | Real-time compliance updates |

---

## 8. Database Schema

### 8.1 Entity Relationship

```
Employee (1) ──── (N) SalaryRecord
Employee (1) ──── (1) LeaveBalance
Employee (1) ──── (N) AttendanceRecord
Employee (1) ──── (N) DisputeTicket
Employee (1) ──── (N) Conversation
Employee (1) ──── (N) Notification
Employee (1) ──── (N) AuditLog
```

### 8.2 Key Tables

**Employee** — 18 records
- Fields: emp_id, name, email, department, designation, grade, location, city_tier, joining_date, role, annual_ctc, tax_regime, rent_paid_monthly

**SalaryRecord** — 108 records (18 employees × 6 months)
- Fields: month, ctc, basic, hra, da, special_allowance, medical, lta, pf_employee, pf_employer, esic_employee, esic_employer, professional_tax, tds, lop_days, lop_deduction, gross_pay, total_deductions, net_pay, bonus, arrears, overtime

**DisputeTicket** — AI review enabled
- Fields: ticket_id, category, description, expected/actual/discrepancy amounts, status, priority, ai_reviewed, ai_verdict, ai_analysis, admin_reviewed, admin_action, admin_notes

**PolicyDocument** — 5 comprehensive documents
- Leave Policy, HRA Policy, Variable Pay Policy, Reimbursement Policy, Code of Conduct & POSH

---

## 9. API Endpoints

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | None | Login, returns JWT |
| GET | `/api/auth/me` | Bearer | Get current user |

### Chat
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/chat` | Bearer | Send message, get AI response |
| GET | `/api/chat/history/{session_id}` | Bearer | Get chat history |
| GET | `/api/chat/sessions` | Bearer | List user's sessions |

### Payroll
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/payroll/{id}/{month}` | Bearer | Get salary record |
| GET | `/api/payroll/{id}/history` | Bearer | Get salary history |
| GET | `/api/payroll/download/{emp_id}/{month}` | Bearer | Download PDF payslip |

### Disputes
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/disputes/my` | Bearer | Employee's disputes |
| GET | `/api/disputes` | HR/Admin | All disputes |
| PATCH | `/api/disputes/{ticket_id}` | HR/Admin | Update dispute |
| POST | `/api/disputes/ai-review/{ticket_id}` | HR/Admin | Trigger AI review |
| POST | `/api/disputes/ai-review-all` | Admin | Batch AI review |
| POST | `/api/disputes/admin-review/{ticket_id}` | Admin | Admin decision |
| GET | `/api/disputes/admin/pending` | Admin | Pending admin review |
| GET | `/api/disputes/admin/all` | Admin | All disputes (admin) |
| GET | `/api/disputes/admin/stats` | Admin | Dispute analytics |

### Other
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/employees/me` | Bearer | My profile |
| GET | `/api/employees` | HR/Admin | All employees |
| GET | `/api/dashboard/stats` | HR/Admin | Dashboard analytics |
| GET | `/api/policies` | Bearer | List policies |
| GET | `/api/audit/logs` | Admin | Audit logs |
| GET | `/api/health` | None | Health check |

---

## 10. Frontend Design

### 10.1 Pages

| Page | Route | Access | Description |
|------|-------|--------|-------------|
| Login | `/login` | Public | Email/password authentication |
| Chat | `/` | Employee, HR | AI chat with 6 agents |
| My Payroll | `/payroll` | Employee, HR | Salary details + PDF download |
| Disputes | `/disputes` | Employee, HR | View/file disputes |
| Policies | `/policies` | Employee, HR | Browse HR policy documents |
| Dashboard | `/dashboard` | HR, Admin | Analytics & query stats |
| Dispute Review | `/admin-disputes` | Admin | AI review + admin oversight |
| Settings | `/settings` | Employee, HR | Profile & preferences |

### 10.2 Design System
- **Color Scheme**: Primary #1e3a5f (dark blue), Accent #3b82f6 (blue)
- **Typography**: Inter font family, 300-800 weights
- **Components**: Cards, tables, modals, badges, charts, toasts
- **Responsive**: Desktop-first, tablet-compatible

### 10.3 Role-Based Navigation

| Role | Visible Pages |
|------|---------------|
| Employee | Chat, Payroll, Disputes, Policies, Settings |
| HR Manager | Chat, Payroll, Disputes, Policies, Dashboard, Settings |
| Admin | Dashboard, Dispute Review (only) |

---

## 11. Security & Compliance

### 11.1 Authentication & Authorization
- JWT-based token authentication (24-hour expiry)
- bcrypt password hashing (direct library, no passlib dependency issues)
- Role-based access control: employee, hr_manager, admin
- API endpoint guards via FastAPI dependency injection

### 11.2 Data Protection
- Employee can only access their own salary/leave data
- HR managers can view all employees but cannot modify payroll
- Admin focused on dispute oversight only
- PAN numbers and bank accounts masked in payslip PDFs

### 11.3 Rate Limiting
- 100 requests/minute per client IP
- Groq API rate limit handling in **`BaseAgent` / `agents/agentic/react_runner.py`**: on 429 / rate-limit errors, one retry using **`GROQ_FALLBACK_MODEL`** (same LangGraph ReAct stack, smaller/faster model)

### 11.4 Audit Trail
- Every chat interaction logged: timestamp, user, query, intent, agent, tools called, response
- Immutable audit log accessible to admin only

---

## 12. Dispute Review System (v2 Feature)

### 12.1 Flow

```
Employee files dispute → Ticket created (status: open)
       ↓
HR/Admin triggers AI Review
       ↓
Dispute Review Agent analyzes:
  - Fetches payroll data
  - Recalculates independently
  - Checks company policies
  - Issues verdict
       ↓
┌──────────────────────────────────────┐
│ Verdict: resolved_invalid            │ → Auto-resolved, employee notified
│ Verdict: resolved_valid              │ → Escalated for admin confirmation
│ Verdict: escalated                   │ → Complex case, admin must decide
└──────────────────────────────────────┘
       ↓
Admin reviews AI analysis
       ↓
Admin action: Approve / Reject / Modify
       ↓
Dispute closed with full audit trail
```

### 12.2 Admin Dashboard Stats
- Total disputes, open count
- AI reviewed count, pending admin review
- Breakdown: AI found discrepancy / no discrepancy / escalated
- Filter by status, AI verdict, admin pending

---

## 13. Project Metrics

| Metric | Value |
|--------|-------|
| Total Files | ~61 source files |
| Python Files (Backend) | 34 files |
| JS/JSX/CSS Files (Frontend) | 27 files |
| AI Agents | 6 |
| Custom Tools | 10 |
| API Endpoints | 22 |
| Frontend Pages | 8 |
| Frontend Components | 10 |
| Database Tables | 9 |
| Seed Data: Employees | 18 |
| Seed Data: Salary Records | 108 |
| Seed Data: Policy Documents | 5 |
| Seed Data: Dispute Tickets | 3 |

---

## 14. Deployment Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key

### Backend Setup
`requirements.txt` pulls **LangChain** (`langchain-core`, `langchain-groq`) and **LangGraph** for the agent runtime, plus FastAPI, SQLAlchemy, and the `groq` package as listed.

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
# Add your GROQ_API_KEY to .env
python seed_data.py
uvicorn main:app --reload --port 8001
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

---

## 15. Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Employee | rahul.sharma@company.com | password123 |
| HR Manager | priya.patel@company.com | password123 |
| Admin | neha.agarwal@company.com | password123 |

### API Keys Required

| Key | Required | Source |
|-----|----------|--------|
| GROQ_API_KEY | **Yes** | https://console.groq.com |
| SERPAPI_KEY | Optional | https://serpapi.com |
| NEWS_API_KEY | Optional | https://newsapi.org |

---

**END OF PROJECT REPORT**

*Prepared by: Gohil Dhruv 
*Date: April 16, 2026*
