import json
import os
import time
from typing import Optional

from openai import OpenAI, AzureOpenAI

from models import ChatResponse, TokenUsage
from prompt import build_system_prompt
from database import execute_query

_sessions: dict[str, list[dict]] = {}

_system_prompt: Optional[str] = None


def _get_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = build_system_prompt()
    return _system_prompt


def _get_client():
    """Returns the appropriate OpenAI client based on PROVIDER env var."""
    provider = os.environ.get("PROVIDER", "openai").lower()

    if provider == "azure":
        return AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-02-01",
        ), os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"), "azure"
    else:
        return OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        ), os.environ.get("MODEL_NAME", "gpt-4o"), "openai"


def chat(session_id: str, message: str) -> ChatResponse:
    """
    Main chat function:
    1. Maintains conversation history per session
    2. Calls OpenAI with system prompt (schema + data as knowledge base)
    3. Parses JSON response → executes SQL on SQLite for validation
    4. Returns ChatResponse
    """
    client, model, provider = _get_client()
    system_prompt = _get_system_prompt()

    if session_id not in _sessions:
        _sessions[session_id] = []

    _sessions[session_id].append({"role": "user", "content": message})

    messages = [{"role": "system", "content": system_prompt}] + _sessions[session_id]

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        latency_ms = int((time.time() - start_time) * 1000)
        raw_content = response.choices[0].message.content

        # Append assistant response to history
        _sessions[session_id].append({"role": "assistant", "content": raw_content})

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            return ChatResponse(
                answer="I had trouble formatting my response. Please try again.",
                query="",
                status="error",
                error="JSON parse error",
                latency_ms=latency_ms,
                provider=provider,
                model=model,
            )

        answer = parsed.get("answer", "")
        sql_query = parsed.get("query", "")
        suggested = parsed.get("suggested_questions", [])

        # Execute SQL on SQLite for internal validation only (silent)
        if sql_query and sql_query.strip().upper().startswith("SELECT"):
            execute_query(sql_query)  # validate silently, don't expose errors to user

        token_usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        return ChatResponse(
            answer=answer,
            query=sql_query,
            suggested_questions=suggested[:5],
            token_usage=token_usage,
            latency_ms=latency_ms,
            provider=provider,
            model=model,
            status="ok",
        )

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return ChatResponse(
            answer=f"An error occurred: {str(e)}",
            query="",
            status="error",
            error=str(e),
            latency_ms=latency_ms,
            provider=provider,
            model=model,
        )


def clear_session(session_id: str) -> None:
    """Clears conversation history for a given session."""
    if session_id in _sessions:
        del _sessions[session_id]
