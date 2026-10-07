"""
LangGraph ReAct agent runner — compiled tool-calling graph for all specialists.

Uses `create_react_agent` so the project follows the standard LangChain agentic pattern
(model ↔ tools loop until a final assistant message without pending tool calls).
"""
from typing import Any, List, Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from agents.agentic.groq_llm import make_chat_groq
from config import GROQ_FALLBACK_MODEL, GROQ_MODEL, MAX_AGENT_ITERATIONS


def _history_messages(conversation_history: Optional[list]) -> List[Any]:
    msgs = []
    if not conversation_history:
        return msgs
    for msg in conversation_history[-10:]:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            msgs.append(AIMessage(content=content))
    return msgs


def _extract_text(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
            else:
                parts.append(str(block))
        return "".join(parts) if parts else ""
    return str(content or "")


def _tools_called_from_messages(messages: List[Any]) -> List[dict]:
    out: List[dict] = []
    round_idx = 0
    for m in messages:
        if not isinstance(m, AIMessage):
            continue
        tcs = getattr(m, "tool_calls", None) or []
        if not tcs:
            continue
        for tc in tcs:
            if isinstance(tc, dict):
                name = tc.get("name")
                args = tc.get("args") or {}
            else:
                name = getattr(tc, "name", None)
                args = getattr(tc, "args", None) or {}
            if name:
                out.append({"tool": name, "args": args, "iteration": round_idx})
        round_idx += 1
    return out


def _final_ai_text(messages: List[Any]) -> str:
    last_ai: Optional[AIMessage] = None
    for m in messages:
        if isinstance(m, AIMessage):
            last_ai = m
    if last_ai is None:
        return ""
    return _extract_text(last_ai) or ""


def run_react_specialist(
    *,
    system_prompt: str,
    user_message: str,
    conversation_history: Optional[list],
    lc_tools: list,
    use_fallback_model: bool = False,
) -> Tuple[str, List[dict]]:
    """
    Run LangGraph ReAct agent. `system_prompt` is passed as the graph `prompt=` (system string).

    Returns (response_text, tools_called) where tools_called matches BaseAgent list shape.
    """
    model_name = GROQ_FALLBACK_MODEL if use_fallback_model else GROQ_MODEL
    llm = make_chat_groq(model_name)

    hist = _history_messages(conversation_history)
    input_messages = [*hist, HumanMessage(content=user_message)]

    # Recursion budget: each tool round is multiple graph steps
    recursion_limit = max(12, MAX_AGENT_ITERATIONS * 2 + 6)
    config = {"recursion_limit": recursion_limit}

    if lc_tools:
        graph = create_react_agent(llm, lc_tools, prompt=system_prompt)
    else:
        graph = create_react_agent(llm, [], prompt=system_prompt)

    result = graph.invoke({"messages": input_messages}, config=config)
    messages_out = result.get("messages") or []

    tools_called = _tools_called_from_messages(list(messages_out))
    text = _final_ai_text(list(messages_out))
    if not text.strip():
        text = "I've completed my analysis. Please let me know if you need more details."
    return text, tools_called
