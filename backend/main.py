from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI, APIStatusError, APITimeoutError

import httpx
import os 
from dotenv import load_dotenv

from websearch.brave import search
from llm import llm

load_dotenv()
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # RUNS ONCE at startup
    app.state.http_client = httpx.AsyncClient()
    app.state.llm_client = AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url=OPENROUTER_BASE_URL,
    )
    yield
    await app.state.http_client.aclose()
    await app.state.llm_client.close()

app = FastAPI(title="FastAPI Dev", version="0.1.0", lifespan=lifespan)

# Middlewares

app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# MODELS
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="The search query.")
    count: int = Field(default=5, ge=1, le=20, description="Number of search results to return.")

class SearchResultItem(BaseModel):  
    title: str
    url: str
    description: str | None = None

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    count: int

class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500, description="The question that the user is asking")
    count: int = Field(default=5, ge=1, le=10, description="Number of search results to use.")

class Citation(BaseModel):
    number: int
    title: str
    url: str

class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    model: str



# ROUTES

@app.get("/health")
async def health_check():
    return {"status:" "ok"}

@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_endpoint(request: SearchRequest):
    client: httpx.AsyncClient = app.state.http_client

    try:
        raw_results = await search(client, request.query, request.count)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=500, detail="Invalid Brave API key")
        elif e.response.status_code == 429:
            raise HTTPException(status_code=429, detail="Brave Search rate limit reached")
        raise HTTPException(status_code=502, detail="Brave Search error")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Brave Search timed out")

    results = [
        SearchResultItem(title=r.title, url=r.url, description=r.description)
        for r in raw_results
    ]
    return SearchResponse(query=request.query, results=results, count=len(results))

@app.post("/ask", response_model=AskResponse, tags=["Ask"])
async def ask_endpoint(request: AskRequest):
    # Step 1: Fetch search reslts from Brave (grounding context)
    # Step 2: Assemble system + user prompt with citations
    # Step 3: Call LLM via OpenRouter
    # Step 4: Return text + structured citations list

    http_client: httpx.AsyncClient = app.state.http_client
    llm_client: AsyncOpenAI = app.state.llm_client

    # Step 1:
    try:
        results = await search(http_client, request.question, request.count)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=500, detail="Invalid Brave API key — check your .env")
        if e.response.status_code == 429:
            raise HTTPException(status_code=429, detail="Brave Search rate limit reached")
        raise HTTPException(status_code=502, detail=f"Brave Search returned {e.response.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Brave Search timed out")

    # Step 2: (already being covered in llm.ask function)
    # Step 3:
    try: 
        answer = await llm.ask(
            client=llm_client,
            question=request.question,
            context=results
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except APIStatusError as e:
        if e.status_code == 401:
            raise HTTPException(status_code=500, detail="Invalid OpenRouter API key")
        if e.status_code == 429:
            raise HTTPException(status_code=429, detail="OpenRouter rate limit reached")
        raise HTTPException(status_code=502, detail=f"OpenRouter error: {e.message}")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="LLM request timed out")

    citations = [
        Citation(number=i+1, title=r.title, url=r.url)
        for i, r in enumerate(results)
    ]

    return AskResponse(
        question=request.question,
        answer=answer,
        citations=citations,
        model=llm.DEFAULT_MODEL,
    )