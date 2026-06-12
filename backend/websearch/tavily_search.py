
import asyncio
import sys
import time
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from tavily import AsyncTavilyClient
from tavily.errors import UsageLimitExceededError, InvalidAPIKeyError

load_dotenv()


load_dotenv()

class SearchResult(BaseModel):
    title: str
    url: str
    content: Optional[str] = None
    description: Optional[str] = None
    age: Optional[str] = None

class TavilyResult(BaseModel):
    title: str
    url: str
    content: str
    score: float

class TavilySearchResponse(BaseModel):
    query: str
    results: list[TavilyResult]

SEARCH_DEPTH = "basic"

async def search(
    client: AsyncTavilyClient,
    query: str,
    count: int = 5,
    offset: int =0,
    depth: str = SEARCH_DEPTH,
) -> list[SearchResult]:
    raw = await client.search(query=query, max_results=count, search_depth=depth)

    try:
        parsed = TavilySearchResponse.model_validate(raw)
    except ValidationError as e:
        raise ValueError(f"Unexpected API response shape: {e}") from e

    return [
        SearchResult(title=r.title, url=r.url, description=r.content)
        for r in parsed.results
    ]

def print_results(results: list[SearchResult]) -> None:
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result.title}")
        print(f"    URL: {result.url}")
        if result.description:
            print(f"    {result.description[:140]}")
        print()


async def main() -> None:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY not set. Add it to your .env file.")
        print("Get a free key (no credit card) at https://app.tavily.com")
        return

    args = sys.argv[1:]
    use_advanced = "--advanced" in args
    query_parts = [a for a in args if a != "--advanced"]
    query = " ".join(query_parts) if query_parts else "what is FastAPI"
    depth: SearchDepth = "advanced" if use_advanced else "basic"

    start = time.perf_counter()
    client = AsyncTavilyClient(api_key=api_key)

    try:
        results = await search(client, query, depth=depth)
    except InvalidAPIKeyError:
        print("Error: Tavily API key invalid. Check TAVILY_API_KEY in .env")
        return
    except UsageLimitExceededError:
        print("Error: Monthly credit limit reached (1,000 free/month). Resets next month.")
        return
    except ValueError as e:
        print(f"Response error: {e}")
        return

    elapsed = time.perf_counter() - start
    print_results(results)
    print(f"Fetched {len(results)} results in {elapsed:.2f}s  [depth={depth}]")


if __name__ == "__main__":
    asyncio.run(main())