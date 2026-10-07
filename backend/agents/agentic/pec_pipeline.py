"""
Planner-Executor-Critic (PEC) workflow for high-stakes decisions.
"""
from typing import Dict, Optional

from config import PEC_ENABLED


def run_pec_review(agent, review_prompt: str, context: Optional[dict] = None) -> Dict:
    """
    Runs a 3-step LLM workflow:
    1) Planner: outline investigation plan
    2) Executor: perform the investigation
    3) Critic: check consistency and suggest confidence/risk
    """
    if not PEC_ENABLED:
        result = agent.run(user_message=review_prompt, context=context or {})
        return {
            "planner": "PEC disabled",
            "executor": result.get("response", ""),
            "critic": "PEC disabled",
            "final_response": result.get("response", ""),
            "confidence": 0.6,
            "risk_score": 0.4,
        }

    plan_prompt = (
        "You are the PLANNER.\n"
        "Create a concise numbered plan to investigate this payroll dispute using available tools.\n"
        "Only output plan steps.\n\n"
        f"{review_prompt}"
    )
    plan_result = agent.run(user_message=plan_prompt, context=context or {})
    planner_text = plan_result.get("response", "")

    exec_prompt = (
        "You are the EXECUTOR.\n"
        "Follow the investigation plan and perform the review.\n"
        "Use tools, provide calculations, and give a draft verdict.\n\n"
        f"Plan:\n{planner_text}\n\n"
        f"Case:\n{review_prompt}"
    )
    exec_result = agent.run(user_message=exec_prompt, context=context or {})
    executor_text = exec_result.get("response", "")

    critic_prompt = (
        "You are the CRITIC.\n"
        "Check the executor analysis for factual/calculation consistency and policy grounding.\n"
        "Return:\n"
        "1) Verdict quality (good/weak)\n"
        "2) Confidence score between 0 and 1\n"
        "3) Risk score between 0 and 1\n"
        "4) Whether to escalate for human approval\n"
        "Keep it concise.\n\n"
        f"Executor output:\n{executor_text}"
    )
    critic_result = agent.run(user_message=critic_prompt, context=context or {})
    critic_text = critic_result.get("response", "")

    confidence = _extract_score(critic_text, "confidence", default=0.65)
    risk_score = _extract_score(critic_text, "risk", default=0.5)

    return {
        "planner": planner_text,
        "executor": executor_text,
        "critic": critic_text,
        "final_response": executor_text,
        "confidence": confidence,
        "risk_score": risk_score,
    }


def _extract_score(text: str, key: str, default: float = 0.5) -> float:
    lower = (text or "").lower()
    anchors = [f"{key} score", key]
    for anchor in anchors:
        idx = lower.find(anchor)
        if idx == -1:
            continue
        window = lower[idx: idx + 60]
        token = ""
        for ch in window:
            if ch.isdigit() or ch == ".":
                token += ch
            elif token:
                break
        try:
            val = float(token)
            if val > 1:
                val = val / 100.0
            return max(0.0, min(1.0, val))
        except Exception:
            pass
    return default

