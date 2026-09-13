# harness_llm.py
"""Shared LLM client factory for every example in this repo.

All examples talk to a single OpenAI-compatible inference endpoint (vLLM)
hosting `openai/gpt-oss-120b`, instead of each example wiring up its own
client. Override the defaults with environment variables if you point this
at a different endpoint/model:

    HARNESS_LLM_BASE_URL   default: https://100.82.5.75:443/v1/
    HARNESS_LLM_MODEL      default: openai/gpt-oss-120b
    HARNESS_LLM_API_KEY    default: "not-needed" (this server does not require auth)
    HARNESS_LLM_VERIFY_SSL default: "false" (the endpoint uses a self-signed cert)
"""

import os
import httpx
from langchain_openai import ChatOpenAI

DEFAULT_BASE_URL = "https://100.82.5.75:443/v1/"
DEFAULT_MODEL = "openai/gpt-oss-120b"


def get_llm(temperature: float = 0, max_completion_tokens: int = 4096) -> ChatOpenAI:
    """Return a ChatOpenAI client configured for the shared inference endpoint.

    `gpt-oss-120b` is a reasoning model: its internal reasoning tokens count
    against `max_completion_tokens`, so code-generation tasks need a generous
    token budget or the response can be truncated before any code is produced.
    """
    base_url = os.environ.get("HARNESS_LLM_BASE_URL", DEFAULT_BASE_URL)
    model = os.environ.get("HARNESS_LLM_MODEL", DEFAULT_MODEL)
    api_key = os.environ.get("HARNESS_LLM_API_KEY", "not-needed")
    verify_ssl = os.environ.get("HARNESS_LLM_VERIFY_SSL", "false").lower() == "true"

    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_completion_tokens=max_completion_tokens,
        http_client=httpx.Client(verify=verify_ssl, timeout=120),
    )
