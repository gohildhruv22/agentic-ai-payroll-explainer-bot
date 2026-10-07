"""
Specialist agent for Indian tax, PF/ESIC, labour compliance, and regulatory updates.

Combines tax calculator, policy RAG, and web search for current rules.
"""
from agents.base_agent import BaseAgent
from tools.tax_calculator import tax_calculator, compute_gratuity
from tools.policy_search_rag import policy_search_rag
from tools.web_search import web_search

SYSTEM_PROMPT = """You are the Compliance Agent for the HR Payroll Explainer Bot.

Your expertise: Indian labour law, tax compliance, statutory deductions, and regulatory updates.

CAPABILITIES:
1. TDS calculation under current Income Tax Act slabs (FY 2025-26)
2. PF (EPF) and ESIC compliance verification
3. Gratuity eligibility and computation
4. Form 16, Form 26AS, and ITR filing guidance
5. Budget announcement impact analysis (via web search)
6. Compliance audit report generation
7. Labour law queries (Factories Act, Shops & Establishments Act, etc.)

RULES:
- ALWAYS cite the relevant Act/Section when answering compliance questions
- Use the web_search tool for the latest budget announcements and regulatory changes
- Use policy_search_rag to check company-specific compliance policies
- Never give definitive legal advice — always recommend consulting a tax professional for complex cases
- Present tax calculations with clear breakdowns showing each slab
- When comparing regimes, always show both with clear recommendation
- Mention important deadlines (e.g., ITR filing dates, Form 16 issuance date)
- All calculations should use FY 2025-26 (AY 2026-27) rates
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tax_calculator",
            "description": "Calculate income tax under Old and/or New regime for FY 2025-26. Returns detailed breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "annual_gross_income": {"type": "number", "description": "Total annual gross income"},
                    "basic_annual": {"type": "number", "description": "Annual basic salary"},
                    "hra_annual": {"type": "number", "description": "Annual HRA received"},
                    "rent_paid_annual": {"type": "number", "description": "Annual rent paid"},
                    "city_tier": {"type": "string", "enum": ["metro", "non_metro"]},
                    "regime": {"type": "string", "enum": ["old", "new", "both"]},
                    "section_80c": {"type": "number", "description": "Section 80C investments"},
                    "section_80d": {"type": "number", "description": "Section 80D premium"}
                },
                "required": ["annual_gross_income"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "policy_search_rag",
            "description": "Search company HR policy documents for compliance-related information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query about policies or compliance"},
                    "top_k": {"type": "integer", "description": "Number of results to return", "default": 3}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for latest tax updates, budget announcements, labour law amendments, EPFO circulars, and Income Tax notifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for web"},
                    "search_type": {"type": "string", "enum": ["general", "news", "tax", "compliance"]}
                },
                "required": ["query"]
            }
        }
    },
]

TOOL_FUNCTIONS = {
    "tax_calculator": tax_calculator,
    "policy_search_rag": policy_search_rag,
    "web_search": web_search,
}


def create_compliance_agent() -> BaseAgent:
    return BaseAgent(
        name="Compliance Agent",
        system_prompt=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_functions=TOOL_FUNCTIONS,
    )
