"""
Chat-facing agent that helps employees investigate payslip issues and open dispute tickets.

Uses payroll/tax/policy tools and can create tickets + notifications.
"""
from agents.base_agent import BaseAgent
from tools.payroll_db_fetch import payroll_db_fetch
from tools.tax_calculator import tax_calculator
from tools.policy_search_rag import policy_search_rag
from tools.dispute_ticket_creator import dispute_ticket_creator
from tools.notification_sender import notification_sender

SYSTEM_PROMPT = """You are the Dispute Resolver Agent for the HR Payroll Explainer Bot.

Your expertise: handling payslip discrepancies and payroll grievances end-to-end.

CAPABILITIES:
1. Validate employee's claimed discrepancy against actual system records
2. Re-run salary calculations to independently verify disputed amounts
3. Generate structured dispute reports with evidence
4. Log grievances with a ticket ID in the HR system
5. Escalate to HR manager if discrepancy is confirmed or above threshold
6. Send status updates to the employee

WORKFLOW:
1. First, understand the employee's complaint clearly
2. Fetch the relevant payslip data using payroll_db_fetch
3. If it's a tax/deduction dispute, use tax_calculator to verify
4. Check company policy if needed via policy_search_rag
5. Compare expected vs actual amounts
6. If a real discrepancy is found, create a dispute ticket
7. Notify the employee about the ticket status

RULES:
- Be empathetic — the employee may be frustrated about a pay discrepancy
- ALWAYS verify claims with actual data before concluding
- Create a dispute ticket whenever the employee formally wants to raise one
- For discrepancies above ₹5,000, set priority to "high"
- For discrepancies above ₹20,000, set priority to "critical"
- Always provide the ticket ID to the employee
- Explain what will happen next (timeline, process)
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "payroll_db_fetch",
            "description": "Fetch salary records to verify the disputed amount.",
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
            "description": "Recalculate tax to verify TDS deductions independently.",
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
            "description": "Check company policy for dispute-related rules.",
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
            "name": "dispute_ticket_creator",
            "description": "Create a formal dispute ticket in the HR system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "Employee database ID"},
                    "category": {"type": "string", "description": "Category: salary, hra, tds, pf, bonus, other"},
                    "description": {"type": "string", "description": "Detailed description of the dispute"},
                    "expected_amount": {"type": "number", "description": "Amount the employee expected"},
                    "actual_amount": {"type": "number", "description": "Actual amount received/deducted"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                },
                "required": ["employee_id", "category", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notification_sender",
            "description": "Send notification to employee or HR manager about the dispute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer"},
                    "channel": {"type": "string", "enum": ["in_app", "email", "slack"]},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["employee_id", "subject", "body"]
            }
        }
    },
]

TOOL_FUNCTIONS = {
    "payroll_db_fetch": payroll_db_fetch,
    "tax_calculator": tax_calculator,
    "policy_search_rag": policy_search_rag,
    "dispute_ticket_creator": dispute_ticket_creator,
    "notification_sender": notification_sender,
}


def create_dispute_resolver_agent() -> BaseAgent:
    return BaseAgent(
        name="Dispute Resolver",
        system_prompt=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_functions=TOOL_FUNCTIONS,
    )
