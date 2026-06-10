import os 
from typing import Optional

from openai import AsyncOpenAI
from brave.brave import SearchResult

OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are a helpful research assistant. Answer the user's question \
using only the search results provided below. Be concise and factual. \
Cite sources by number [1], [2], etc. inline at the end of relevant sentences. \
If the search results do not contain enough information to answer the question, \
say so — do not invent facts."""

async def ask(
        client: AsyncOpenAI,
        question: str,
        context: list[SearchResult],
        model: str = DEFAULT_MODEL,
) -> str:
    api_key = os.environ["OPENROUTER_API_KEY"]
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in env")
    
    user_prompt = _build_user_prompt(question, context)
    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.3,
    )

    return completion.choices[0].message.content or ""


def _build_user_prompt(question: str, context: list[SearchResult]) -> str:
    """
    Format search results into a numbered context block for LLM
    """
    lines = ["Search results:\n"]
    for i, result in enumerate(context, start=1):
        lines.append(f"[{i}] Title: {result.title}")
        lines.append(f"    URL: {result.url}")
        if result.description:
            lines.append(f"    {result.description}")
        lines.append("")
    lines.append(f"Question: {question}")
    return "\n".join(lines)

def make_client() -> AsyncOpenAI:
    """Create an async OpenaAI client configured to user OpenRouter"""
    return AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url=OPENROUTER_BASE_URL,
    )