"""
Specialist agent for salary, payslip, and CTC questions.

Uses tools to read real payroll/leave data and tax helpers — answers must come from DB/tools, not guesses.
"""
from agents.base_agent import BaseAgent
from tools.payroll_db_fetch import payroll_db_fetch
from tools.tax_calculator import (
    tax_calculator, compute_pf, compute_esic,
    compute_professional_tax, compute_hra_exemption, compute_gratuity
)
from tools.leave_attendance_fetch import leave_attendance_fetch
from tools.payslip_generator import payslip_generator

SYSTEM_PROMPT = """You are the Payroll Calculator Agent for the HR Payroll Explainer Bot.

Your expertise: salary computation, CTC breakdown, deduction explanations, and payslip generation.

CAPABILITIES:
1. Retrieve salary records for any month and explain each component
2. Calculate gross pay from CTC structure
3. Explain PF, ESIC, Professional Tax deductions
4. Calculate HRA exemption based on city tier and rent paid
5. Handle overtime, arrears, and bonus calculations
6. Compare Old vs New tax regime and recommend the optimal one
7. Explain month-over-month salary changes
8. Generate downloadable payslip PDFs

RULES:
- ALWAYS use tools to fetch actual data. NEVER fabricate salary figures.
- Present salary data in clear, structured tables
- Explain each component in simple, plain language
- When comparing months, highlight what changed and why
- Format all amounts in Indian Rupee (₹) with comma separators
- If asked about tax regimes, always calculate BOTH and show comparison
- Include actionable insights (e.g., "You can save ₹X by switching to New Regime")
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "payroll_db_fetch",
            "description": "Fetch salary records for an employee from the payroll database. Can fetch for a specific month or all months.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "The employee's database ID"},
                    "month": {"type": "string", "description": "Month in YYYY-MM format (e.g., 2026-04). If not provided, fetches all records."}
                },
                "required": ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tax_calculator",
            "description": "Calculate income tax under Old and/or New regime for FY 2025-26. Returns detailed tax breakdown with slabs, deductions, and recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "annual_gross_income": {"type": "number", "description": "Total annual gross income"},
                    "basic_annual": {"type": "number", "description": "Annual basic salary"},
                    "hra_annual": {"type": "number", "description": "Annual HRA received"},
                    "rent_paid_annual": {"type": "number", "description": "Annual rent paid by employee"},
                    "city_tier": {"type": "string", "enum": ["metro", "non_metro"], "description": "City classification"},
                    "regime": {"type": "string", "enum": ["old", "new", "both"], "description": "Which tax regime to calculate"},
                    "section_80c": {"type": "number", "description": "Section 80C investments (max 1.5L)"},
                    "section_80d": {"type": "number", "description": "Section 80D medical insurance premium"}
                },
                "required": ["annual_gross_income"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "leave_attendance_fetch",
            "description": "Fetch leave balance and attendance records for an employee.",
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
    {
        "type": "function",
        "function": {
            "name": "payslip_generator",
            "description": "Generate a PDF payslip for an employee for a specific month. Returns a download link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "The employee's database ID"},
                    "month": {"type": "string", "description": "Month in YYYY-MM format"}
                },
                "required": ["employee_id", "month"]
            }
        }
    },
]

TOOL_FUNCTIONS = {
    "payroll_db_fetch": payroll_db_fetch,
    "tax_calculator": tax_calculator,
    "leave_attendance_fetch": leave_attendance_fetch,
    "payslip_generator": payslip_generator,
}


def create_payroll_calculator_agent() -> BaseAgent:
    return BaseAgent(
        name="Payroll Calculator",
        system_prompt=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_functions=TOOL_FUNCTIONS,
    )
