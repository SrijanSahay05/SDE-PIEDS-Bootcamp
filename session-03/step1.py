import asyncio
import httpx
import json 
import os 

from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

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
        count: int=5,
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

def print_results(results: list[SearchResult]) -> None:
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result.title}")
        print(f"    URL: {result.url}")
        if result.description:
            print(f"    {result.description[:140]}")
        print()


async def main() -> None:
    api = os.environ["BRAVE_API_KEY"]
    if not api:
        raise ValueError("BRAVE_API_KEY not found. Please set it up in .env ifle")
    query = "What is FastAPI?"
    try:
        async with httpx.AsyncClient() as client:
            results = await search(client=client, query=query)
    except httpx.HTTPStatusError as e:
        if e.response.status_code==401:
            print("Error: Invalid API key.   Check your BRAVE_API_KEY in .env")()
        elif e.response.status_code==429:
            print("Error: Rate limit exceeded. Wait a moment and retry.")
        else: 
            print(f"HTTP error {e.response.status_code} : {e}")

    except httpx.ConnectTimeout:
        print("Error: Request timed out.")
        return
    
    print_results(results=results)

if __name__=="__main__":
    asyncio.run(main())
