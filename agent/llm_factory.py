"""
Provider factory shared by the v2 agents (same routing as the v1 StaticAgent;
kept separate so v1 code stays frozen).  Temperature is a parameter and is
logged in every output row.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def make_llm(model_name: str, temperature: float = 0.2):
    name = model_name.lower()
    if "gemini" in name:
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY missing.")
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=key)
    if model_name.startswith("openrouter/"):
        from langchain_openai import ChatOpenAI
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY missing.")
        return ChatOpenAI(model=model_name[len("openrouter/"):], temperature=temperature, api_key=key,
                          base_url="https://openrouter.ai/api/v1")
    if model_name.startswith("vllm/"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name[len("vllm/"):], temperature=temperature,
                          api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
                          base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"))
    if "claude" in name:
        from langchain_anthropic import ChatAnthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY missing.")
        return ChatAnthropic(model=model_name, temperature=temperature, anthropic_api_key=key)
    if "gpt" in name:
        from langchain_openai import ChatOpenAI
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY missing.")
        return ChatOpenAI(model=model_name, temperature=temperature, api_key=key)
    if "deepseek" in name:
        from langchain_openai import ChatOpenAI
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise ValueError("DEEPSEEK_API_KEY missing.")
        return ChatOpenAI(model=model_name, temperature=temperature, api_key=key, base_url="https://api.deepseek.com")
    raise ValueError(f"Unsupported model name: {model_name}")
