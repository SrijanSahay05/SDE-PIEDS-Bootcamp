from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

import httpx
# from brave import search # our serach module 
from brave.brave import search


@asynccontextmanager
async def lifespan(app: FastAPI):
    # RUNS ONCE at startup
    app.state.http_client = httpx.AsyncClient()
    yield
    await app.state.http_client.aclose()

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


# ROUTES

@app.get("/health")
async def health_check():
    return {"status:" "ok"}

@app.post("/search", response_model=SearchResponse)
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