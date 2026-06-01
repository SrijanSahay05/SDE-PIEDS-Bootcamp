import asyncio
import httpx
import json
import os 

from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["BRAVE_API_KEY"]

class SearchResult(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    age: Optional[str] = None

class WebResults(BaseModel):
    results: list[SearchResult]

class BraveSearchResponse(BaseModel):
    web: WebResults

async def search(
        client: httpx.AsyncClient,
        query: str,
        count: int = 5,
) -> list[SearchResult]:
    response = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "X-Subscription-Token": api_key,
                "Accept": "application/json",
            },
            params={"q": query, "count": 3},
            timeout=10,
        )
    response.raise_for_status()
    parsed = BraveSearchResponse.model_validate(response.json())
    return parsed.web.results
    
async def main() -> None:
    async with httpx.AsyncClient() as client:
        results = await search(client, "FastAPI tutorial")

    for i, result in enumerate(results, 1):
        print(f"[{i}] {result.title}")
        print(f"   {result.url}")
        if result.description:
            print(f"    {result.description[:120]}")
        print()


asyncio.run(main())

