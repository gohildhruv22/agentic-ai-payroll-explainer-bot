"""
Specialist agent wrapper: LangChain ChatGroq + LangGraph ReAct (`create_react_agent`).

All domain agents (payroll, compliance, policy, dispute, general, dispute review) use this
same agentic stack — shared tool wiring and a compiled LangGraph tool-calling loop.
"""
from typing import Optional

from agents.agentic.react_runner import run_react_specialist
from agents.agentic.tools_builder import build_structured_tools
from config import GROQ_API_KEY


class BaseAgent:
    def __init__(self, name: str, system_prompt: str, tools: list = None, tool_functions: dict = None):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.tool_functions = tool_functions or {}

    def run(
        self,
        user_message: str,
        context: dict = None,
        conversation_history: list = None,
    ) -> dict:
        if not GROQ_API_KEY:
            return {
                "success": False,
                "response": "Groq API key not configured. Please set GROQ_API_KEY in .env file.",
                "agent": self.name,
                "tools_called": [],
            }

        lc_tools = (
            build_structured_tools(self.tools, self.tool_functions)
            if self.tool_functions
            else []
        )
        system = self._build_system_prompt(context)
        self.tools_called = []

        text: Optional[str] = None
        try:
            text, self.tools_called = run_react_specialist(
                system_prompt=system,
                user_message=user_message,
                conversation_history=conversation_history or [],
                lc_tools=lc_tools,
                use_fallback_model=False,
            )
        except Exception as e:
            error_msg = str(e)
            err = error_msg.lower()
            if "rate_limit" not in err and "429" not in err:
                return self._error_response(
                    f"Error communicating with AI service: {error_msg}"
                )
            try:
                text, self.tools_called = run_react_specialist(
                    system_prompt=system,
                    user_message=user_message,
                    conversation_history=conversation_history or [],
                    lc_tools=lc_tools,
                    use_fallback_model=True,
                )
            except Exception:
                return self._error_response(
                    "API rate limited on both models. Please try again in a few minutes."
                )

        return {
            "success": True,
            "response": text or "I apologize, I could not generate a response.",
            "agent": self.name,
            "tools_called": self.tools_called,
        }

    def _build_system_prompt(self, context: dict = None) -> str:
        prompt = self.system_prompt
        if context:
            prompt += f"\n\nCurrent Context:\n"
            if "employee" in context:
                emp = context["employee"]
                prompt += f"- Employee: {emp.get('name', 'Unknown')} (ID: {emp.get('id', 'N/A')})\n"
                prompt += f"- Department: {emp.get('department', 'N/A')}\n"
                prompt += f"- Designation: {emp.get('designation', 'N/A')}\n"
                prompt += f"- Location: {emp.get('location', 'N/A')} ({emp.get('city_tier', 'N/A')})\n"
                prompt += f"- Annual CTC: ₹{emp.get('annual_ctc', 0):,.0f}\n"
                prompt += f"- Tax Regime: {emp.get('tax_regime', 'new')}\n"
                prompt += f"- Rent Paid Monthly: ₹{emp.get('rent_paid_monthly', 0):,.0f}\n"
            if "current_date" in context:
                prompt += f"- Current Date: {context['current_date']}\n"
        return prompt

    def _error_response(self, error_msg: str) -> dict:
        return {
            "success": False,
            "response": error_msg,
            "agent": self.name,
            "tools_called": getattr(self, "tools_called", []),
        }
