"""Shared LangChain ChatGroq factory — single place for Groq model settings."""
from langchain_groq import ChatGroq

from config import GROQ_API_KEY


def make_chat_groq(model: str, temperature: float = 0.3, max_tokens: int = 4096) -> ChatGroq:
    kwargs = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if GROQ_API_KEY:
        kwargs["groq_api_key"] = GROQ_API_KEY
    try:
        return ChatGroq(model=model, **kwargs)
    except TypeError:
        return ChatGroq(model_name=model, **kwargs)
