"""
Intent → specialist agent factory. Central registry for the orchestrator (multi-agent routing).

Factories return BaseAgent instances configured per domain (LangChain + LangGraph under the hood).
"""

from typing import Callable, Dict, List, Optional, Tuple

# (display_name, factory)
_SpecialistEntry = Tuple[str, Callable]


def _build_map() -> Dict[str, _SpecialistEntry]:
    from agents.payroll_calculator import create_payroll_calculator_agent
    from agents.compliance_agent import create_compliance_agent
    from agents.policy_explainer import create_policy_explainer_agent
    from agents.dispute_resolver import create_dispute_resolver_agent

    return {
        "salary": ("Payroll Calculator", create_payroll_calculator_agent),
        "tax": ("Compliance Agent", create_compliance_agent),
        "compliance": ("Compliance Agent", create_compliance_agent),
        "policy": ("Policy Explainer", create_policy_explainer_agent),
        "dispute": ("Dispute Resolver", create_dispute_resolver_agent),
    }


_MAP: Optional[Dict[str, _SpecialistEntry]] = None


def specialist_map() -> Dict[str, _SpecialistEntry]:
    global _MAP
    if _MAP is None:
        _MAP = _build_map()
    return _MAP


def get_specialist_factory(intent: str) -> Optional[_SpecialistEntry]:
    return specialist_map().get(intent)


def list_intent_keys() -> List[str]:
    return list(specialist_map().keys())
