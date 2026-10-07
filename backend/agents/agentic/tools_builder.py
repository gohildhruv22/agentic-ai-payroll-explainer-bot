"""Convert OpenAI-style tool metadata + callables into LangChain StructuredTools."""
from typing import Callable, Dict, List

from langchain_core.tools import StructuredTool


def tool_description(tool_specs: list, tool_name: str) -> str:
    for t in tool_specs or []:
        if t.get("type") != "function":
            continue
        fn = t.get("function") or {}
        if fn.get("name") == tool_name:
            return (fn.get("description") or "").strip() or f"Tool: {tool_name}"
    return f"Execute {tool_name}."


def build_structured_tools(
    tool_specs: list,
    tool_functions: Dict[str, Callable],
) -> List[StructuredTool]:
    tools: List[StructuredTool] = []
    for name, func in tool_functions.items():
        desc = tool_description(tool_specs, name)
        tools.append(StructuredTool.from_function(func, name=name, description=desc))
    return tools
