"""
Routes each user message to the right specialist agent (payroll, tax, policy, dispute, etc.).

Uses the agentic registry (LangChain + LangGraph specialists) and keyword intent scoring.
Logs activity via audit_logger.
"""
import json
import re
from datetime import datetime
from agents.base_agent import BaseAgent
from agents.agentic.registry import get_specialist_factory
from tools.employee_profile_fetch import employee_profile_fetch
from tools.audit_logger import audit_logger
from tools.payroll_db_fetch import payroll_db_fetch as pdb
from tools.leave_attendance_fetch import leave_attendance_fetch as laf
from tools.policy_search_rag import policy_search_rag as psr
from tools.agent_memory_fetch import agent_memory_fetch


# Simple keyword overlap scoring — highest score wins as the "intent" bucket
INTENT_KEYWORDS = {
    "salary": [
        "salary", "take-home", "take home", "net pay", "gross pay", "ctc", "payslip",
        "pay slip", "earnings", "basic", "allowance", "hra", "da", "special allowance",
        "lta", "medical", "bonus", "arrears", "overtime", "increment", "hike",
        "salary breakdown", "salary structure", "monthly salary", "in-hand",
        "deduction", "paycheck", "compensation", "how much do i earn", "what is my salary",
    ],
    "tax": [
        "tax", "tds", "income tax", "old regime", "new regime", "tax slab", "tax saving",
        "80c", "80d", "section 80", "tax planning", "tax calculation", "hra exemption",
        "tax deducted", "form 16", "form 26as", "itr", "tax return", "tax regime",
        "which regime", "compare regime", "tax liability", "taxable income",
    ],
    "compliance": [
        "pf", "provident fund", "epf", "esic", "esi", "gratuity", "professional tax",
        "labour law", "labor law", "compliance", "statutory", "epfo", "pension",
        "factories act", "shops and establishment", "minimum wage", "lwf",
        "labour welfare", "budget", "union budget", "amendment",
        "news", "latest updates", "current updates", "market news", "regulatory updates",
        "latest news", "recent changes", "what's new", "new rules",
    ],
    "policy": [
        "leave", "leave policy", "earned leave", "sick leave", "casual leave",
        "maternity", "paternity", "encashment", "carry forward", "leave balance",
        "notice period", "probation", "full and final", "f&f", "reimbursement",
        "travel policy", "medical reimbursement", "work from home", "wfh",
        "posh", "code of conduct", "grievance", "appraisal", "variable pay",
        "increment policy", "attendance", "absent", "lop", "loss of pay",
        "how many leaves", "holiday", "comp off",
    ],
    "dispute": [
        "dispute", "wrong", "incorrect", "discrepancy", "error", "mistake",
        "not correct", "missing", "extra deduction", "less salary", "over deducted",
        "underpaid", "overpaid", "complaint", "grievance", "raise ticket",
        "file dispute", "salary mismatch", "wrong deduction", "problem with",
        "issue with my", "not matching",
    ],
}


def classify_intent(query: str) -> tuple[str, float]:
    query_lower = query.lower()
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[intent] = score

    if not scores:
        return "general", 0.0

    best_intent = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = round(scores[best_intent] / max(1, total), 2)
    return best_intent, confidence


class OrchestratorAgent:
    def process_query(
        self,
        user_message: str,
        employee_id: int,
        session_id: str,
        conversation_history: list = None,
    ) -> dict:
        profile_result = employee_profile_fetch(employee_id=employee_id)
        if not profile_result.get("success"):
            return {
                "response": "Unable to retrieve your employee profile. Please contact HR.",
                "agent": "Orchestrator",
                "intent": "error",
                "tools_called": [],
            }

        employee = profile_result["employee"]
        memory_result = agent_memory_fetch(employee_id=employee_id)
        memories = memory_result.get("memories", []) if memory_result.get("success") else []
        context = {
            "employee": employee,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "memory": memories[:10],
        }

        intent, confidence = classify_intent(user_message)

        specialist = get_specialist_factory(intent) if confidence >= 0.35 else None
        if specialist:
            agent_name, agent_factory = specialist
            agent = agent_factory()
        else:
            agent = self._create_general_agent()
            agent_name = "General Assistant"

        enriched_message = self._enrich_message(user_message, employee, intent, memories)

        result = agent.run(
            user_message=enriched_message,
            context=context,
            conversation_history=conversation_history,
        )
        approval_gate = self._detect_sensitive_action(user_message, intent, confidence)
        if approval_gate["requires_human_approval"]:
            response = result.get("response", "")
            response += (
                "\n\nSafety note: This request appears to involve a high-impact account/payroll action. "
                "A human HR/admin approval is required before any final change can be applied."
            )
            result["response"] = response
            result["requires_human_approval"] = True
            result["approval_reason"] = approval_gate["reason"]
        else:
            result["requires_human_approval"] = False

        audit_logger(
            user_id=employee_id,
            query_text=user_message,
            intent=intent,
            agent_used=agent_name,
            tools_called=result.get("tools_called", []),
            response_summary=result.get("response", "")[:200],
            escalation_triggered=False,
        )

        result["intent"] = intent
        result["intent_confidence"] = confidence
        result["agent"] = agent_name
        return result

    def _detect_sensitive_action(self, user_message: str, intent: str, confidence: float) -> dict:
        text = (user_message or "").lower()
        sensitive_terms = [
            "change my tax regime",
            "switch my regime",
            "correct my salary",
            "fix my payslip",
            "update payroll",
            "modify deduction",
            "apply correction",
            "change my bank account",
        ]
        if any(term in text for term in sensitive_terms):
            return {"requires_human_approval": True, "reason": "User requested a high-impact payroll/profile change."}
        if intent in ("salary", "tax", "dispute") and confidence < 0.4 and any(k in text for k in ["change", "update", "fix", "correct"]):
            return {"requires_human_approval": True, "reason": "Low-confidence high-impact request."}
        return {"requires_human_approval": False, "reason": ""}

    def _enrich_message(self, message: str, employee: dict, intent: str, memories: list) -> str:
        enrichment = f"\n\n[System Context - Employee: {employee['name']} (ID: {employee['id']})"
        enrichment += f", Dept: {employee['department']}, CTC: ₹{employee['annual_ctc']:,.0f}"
        enrichment += f", Tax Regime: {employee['tax_regime']}"
        enrichment += f", Location: {employee['location']} ({employee['city_tier']})"
        enrichment += f", Monthly Rent: ₹{employee['rent_paid_monthly']:,.0f}]"
        if memories:
            pairs = [f"{m.get('key')}={m.get('value')}" for m in memories[:5]]
            enrichment += f"\n[Memory: {'; '.join(pairs)}]"

        return message + enrichment

    def _create_general_agent(self) -> BaseAgent:
        system_prompt = """You are the General HR Assistant for the Payroll Explainer Bot.

You help with general HR queries that don't fall into specific categories.
You have access to employee data, payroll records, leave information, and company policies.

RULES:
- Be helpful, professional, and empathetic
- Use tools to fetch real data - never make up information
- If a query is clearly about salary/tax/compliance/policy/dispute, handle it appropriately
- For anything outside your capabilities, politely redirect to HR
- Keep responses concise but complete
"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "payroll_db_fetch",
                    "description": "Fetch salary records for an employee.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer"},
                            "month": {"type": "string"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "leave_attendance_fetch",
                    "description": "Fetch leave balance and attendance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "integer"},
                            "month": {"type": "string"}
                        },
                        "required": ["employee_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "policy_search_rag",
                    "description": "Search company HR policy documents.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "top_k": {"type": "integer", "default": 3}
                        },
                        "required": ["query"]
                    }
                }
            },
        ]

        return BaseAgent(
            name="General Assistant",
            system_prompt=system_prompt,
            tools=tools,
            tool_functions={
                "payroll_db_fetch": pdb,
                "leave_attendance_fetch": laf,
                "policy_search_rag": psr,
            },
        )
