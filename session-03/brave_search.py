"""
brave_search.py — Typed, async Brave Search API wrapper.

Usage:
    python brave_search.py "what is FastAPI"

Requires:
    BRAVE_API_KEY set in .env (copy .env.example → .env and fill in the key)

Install deps:
    pip install httpx pydantic python-dotenv
"""

import asyncio
import sys
import time
import httpx
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()

API_BASE = "https://api.search.brave.com/res/v1/web/search"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class SearchResult(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    age: Optional[str] = None


class WebResults(BaseModel):
    results: list[SearchResult]


class BraveSearchResponse(BaseModel):
    web: WebResults


# ---------------------------------------------------------------------------
# Core search function
# ---------------------------------------------------------------------------

async def search(
    client: httpx.AsyncClient,
    query: str,
    count: int = 5,
    offset: int = 0,
) -> list[SearchResult]:
    """
    Search the web via Brave Search API.

    Args:
        client: An active httpx.AsyncClient (caller manages the connection pool).
        query:  The search query string.
        count:  Number of results to return (1–20, default 5).
        offset: Pagination offset (0–9, default 0).

    Returns:
        A list of SearchResult objects, fully typed and validated.

    Raises:
        httpx.HTTPStatusError: On 4xx/5xx responses (401, 429, etc.).
        ValueError: If the API response doesn't match the expected schema.
    """
    response = await client.get(
        API_BASE,
        headers={
            "X-Subscription-Token": os.environ["BRAVE_API_KEY"],
            "Accept": "application/json",
        },
        params={"q": query, "count": count, "offset": offset},
        timeout=10,
    )
    response.raise_for_status()

    try:
        parsed = BraveSearchResponse.model_validate(response.json())
    except ValidationError as e:
        raise ValueError(f"Unexpected API response shape: {e}") from e

    return parsed.web.results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_results(results: list[SearchResult]) -> None:
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result.title}")
        print(f"    URL: {result.url}")
        if result.description:
            print(f"    {result.description[:140]}")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        raise ValueError("BRAVE_API_KEY not set. Add it to your .env file.")

    query = sys.argv[1] if len(sys.argv) > 1 else "what is FastAPI"
    start = time.perf_counter()

    try:
        async with httpx.AsyncClient() as client:
            results = await search(client, query)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Error: Invalid API key. Check your BRAVE_API_KEY in .env")
        elif e.response.status_code == 429:
            print("Error: Rate limit exceeded. Wait a moment and retry.")
        else:
            print(f"HTTP error {e.response.status_code}: {e}")
        return
    except httpx.ConnectTimeout:
        print("Error: Request timed out.")
        return

    elapsed = time.perf_counter() - start
    print_results(results)
    print(f"Fetched {len(results)} results in {elapsed:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
