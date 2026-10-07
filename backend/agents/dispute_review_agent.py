"""
Backend-only agent for automatic review of dispute tickets (valid / invalid / escalate).

Invoked from API routes to populate AI verdict fields on DisputeTicket rows.
"""
from agents.base_agent import BaseAgent
from tools.payroll_db_fetch import payroll_db_fetch
from tools.tax_calculator import tax_calculator
from tools.policy_search_rag import policy_search_rag
from tools.leave_attendance_fetch import leave_attendance_fetch

SYSTEM_PROMPT = """You are the Dispute Review Agent for the HR Payroll Explainer Bot.

Your job is to AUTOMATICALLY REVIEW open dispute tickets by analyzing the employee's payroll data,
recalculating the expected values, and determining whether the dispute is valid.

WORKFLOW:
1. Read the dispute details (category, description, expected_amount, actual_amount)
2. Fetch the employee's salary record for the relevant month
3. If it's a tax/deduction dispute, use tax_calculator to independently verify
4. If it's a policy dispute, use policy_search_rag to check rules
5. Compare your calculated values against the dispute claim
6. Make a VERDICT:
   - "resolved_valid" — The employee is RIGHT. There IS a discrepancy. Flag for admin review.
   - "resolved_invalid" — The employee is WRONG. The payroll is correct. Provide explanation.
   - "escalated" — The issue is complex, involves amounts > ₹20,000, or you cannot determine. Escalate to admin.

RESPONSE FORMAT:
Always respond with a structured analysis:
1. **Dispute Summary**: Brief description of what was claimed
2. **Investigation**: What you checked and the data you found
3. **Calculation**: Your independent calculation (if applicable)
4. **Verdict**: resolved_valid / resolved_invalid / escalated
5. **Resolution Notes**: Clear explanation of your findings
6. **Recommendation**: What action should be taken

RULES:
- ALWAYS use tools to fetch real data — never guess
- Be fair and thorough — check all angles
- For amounts > ₹20,000 discrepancy, always escalate to admin
- For complex multi-component disputes, escalate to admin
- Provide clear, detailed explanations that admin can review
- Be empathetic in your resolution notes — these will be shown to employees
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "payroll_db_fetch",
            "description": "Fetch salary records to verify disputed amounts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "Employee database ID"},
                    "month": {"type": "string", "description": "Month in YYYY-MM format"}
                },
                "required": ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tax_calculator",
            "description": "Recalculate tax/deductions to verify correctness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "annual_gross_income": {"type": "number"},
                    "basic_annual": {"type": "number"},
                    "hra_annual": {"type": "number"},
                    "rent_paid_annual": {"type": "number"},
                    "city_tier": {"type": "string", "enum": ["metro", "non_metro"]},
                    "regime": {"type": "string", "enum": ["old", "new", "both"]}
                },
                "required": ["annual_gross_income"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "policy_search_rag",
            "description": "Check company policy for rules related to the dispute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Policy search query"},
                    "top_k": {"type": "integer", "default": 3}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "leave_attendance_fetch",
            "description": "Fetch leave and attendance data to verify LOP-related disputes.",
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
]

TOOL_FUNCTIONS = {
    "payroll_db_fetch": payroll_db_fetch,
    "tax_calculator": tax_calculator,
    "policy_search_rag": policy_search_rag,
    "leave_attendance_fetch": leave_attendance_fetch,
}


def create_dispute_review_agent() -> BaseAgent:
    return BaseAgent(
        name="Dispute Review Agent",
        system_prompt=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_functions=TOOL_FUNCTIONS,
    )
