"""
Specialist agent for company HR policy Q&A (leave, reimbursements, conduct, etc.).

Primarily uses policy_search_rag and leave balance tools before answering.
"""
from agents.base_agent import BaseAgent
from tools.policy_search_rag import policy_search_rag
from tools.leave_attendance_fetch import leave_attendance_fetch

SYSTEM_PROMPT = """You are the Policy Explainer Agent for the HR Payroll Explainer Bot.

Your expertise: explaining company HR policies in plain, easy-to-understand language.

CAPABILITIES:
1. Leave policy: types (EL, SL, CL, etc.), accrual rules, encashment, carry-forward
2. Variable pay, appraisal cycle, and increment policy
3. Reimbursement policies: travel, medical, mobile, work-from-home
4. Probation period, notice period, and full-and-final settlement
5. Maternity, paternity, and compassionate leave entitlements
6. POSH (Prevention of Sexual Harassment) policy
7. Code of conduct and grievance redressal procedures

RULES:
- ALWAYS use the policy_search_rag tool to find relevant policy sections before answering
- Quote exact policy text when relevant, with source document reference
- If the policy document doesn't cover the question, clearly state that
- Use simple, jargon-free language
- Present information in structured format with headers and bullet points
- When discussing leave, always include the employee's current leave balance if available
- Never make up policy rules that aren't in the documents
- If a question is ambiguous, ask for clarification
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "policy_search_rag",
            "description": "Search company HR policy documents using semantic search. Returns relevant policy excerpts with source citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The policy-related question or topic to search for"},
                    "top_k": {"type": "integer", "description": "Number of results to return", "default": 3}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "leave_attendance_fetch",
            "description": "Fetch an employee's leave balance and attendance records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "The employee's database ID"},
                    "month": {"type": "string", "description": "Specific month in YYYY-MM format"}
                },
                "required": ["employee_id"]
            }
        }
    },
]

TOOL_FUNCTIONS = {
    "policy_search_rag": policy_search_rag,
    "leave_attendance_fetch": leave_attendance_fetch,
}


def create_policy_explainer_agent() -> BaseAgent:
    return BaseAgent(
        name="Policy Explainer",
        system_prompt=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_functions=TOOL_FUNCTIONS,
    )
