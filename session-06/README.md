# Session 06 — Tavily Search & the `/ask` Endpoint

**Goal:** Swap Brave Search for Tavily (simpler API, no manual HTTP), wire it into the FastAPI backend's `/ask` endpoint, and end up with a full search-and-answer pipeline: question in, cited LLM answer out.

---

## Setup

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install Tavily
pip install tavily-python python-dotenv

# Verify
python3 -c "from tavily import TavilyClient; print('tavily ok')"
```

You need a **Tavily API key**:

1. Go to [app.tavily.com](https://app.tavily.com) and sign in with Google
2. Your API key is shown on the dashboard immediately — no credit card required
3. Free tier: **1,000 searches/month**
4. Add it to `.env`:

```
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Why Switch from Brave to Tavily?

Brave Search requires manual HTTP setup: you create an `httpx.AsyncClient`, set custom headers, parse the JSON response yourself, and validate it with Pydantic. That's good learning (Session 3), but it's friction once you already understand the pattern.

Tavily ships a Python SDK that handles all of that:

```python
# Brave Search — you manage everything
async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
        params={"q": query, "count": count},
        timeout=10,
    )
    response.raise_for_status()
    parsed = BraveSearchResponse.model_validate(response.json())
    return parsed.web.results

# Tavily — the SDK handles HTTP, auth, and parsing
client = AsyncTavilyClient(api_key=api_key)
raw = await client.search(query=query, max_results=count)
```

Tavily also returns a `content` field — a short snippet of the actual page content, not just the meta description — which gives the LLM better context for each source.

---

## Walking Through `01_tavily.py`

```python
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
response = tavily_client.search("Who is Leo Messi?")

print(response)
```

This is the minimum viable Tavily call: create a client, call `.search()`, print the result. No `httpx`, no Pydantic, no `asyncio.run()` — just the SDK.

The response is a dict with a `results` key containing a list of dicts, each with `title`, `url`, `content`, and a relevance `score`. In the backend we wrap these in a Pydantic `SearchResult` model before passing them to the LLM.

**Note**: This uses the synchronous `TavilyClient`. The backend uses `AsyncTavilyClient` inside FastAPI routes — same API, async version — so the knowledge transfers directly.

---

## The Full Pipeline: How the Backend Uses Tavily

`01_tavily.py` is the proof-of-concept. The real action happens in `backend/websearch/tavily_search.py` and `backend/main.py`.

### `backend/websearch/tavily_search.py`

This module adapts the raw Tavily response into our internal `SearchResult` type so the rest of the code doesn't need to know which search provider we're using:

```python
class SearchResult(BaseModel):
    title: str
    url: str
    content: Optional[str] = None
    description: Optional[str] = None

async def search(
    client: AsyncTavilyClient,
    query: str,
    count: int = 5,
    depth: str = "basic",
) -> list[SearchResult]:
    raw = await client.search(query=query, max_results=count, search_depth=depth)
    parsed = TavilySearchResponse.model_validate(raw)
    return [
        SearchResult(title=r.title, url=r.url, description=r.content)
        for r in parsed.results
    ]
```

The function signature matches the old Brave `search()` — `(client, query, count)` → `list[SearchResult]`. The LLM module doesn't need to change at all; we just swap the import.

### `backend/main.py` — the `/ask` endpoint

The `/ask` endpoint runs two steps in sequence:

```python
@app.post("/ask", response_model=AskResponse, tags=["Ask"])
async def ask_endpoint(request: AskRequest):
    tavily_client: AsyncTavilyClient = app.state.tavily_client
    llm_client: AsyncOpenAI = app.state.llm_client

    # Step 1: search the web (Tavily)
    results = await search(tavily_client, request.question, request.count)

    # Step 2: send results + question to the LLM (OpenRouter)
    answer = await llm.ask(
        client=llm_client,
        question=request.question,
        context=results,
    )

    # Step 3: build structured citations from the same results list
    citations = [
        Citation(number=i + 1, title=r.title, url=r.url)
        for i, r in enumerate(results)
    ]

    return AskResponse(
        question=request.question,
        answer=answer,
        citations=citations,
        model=llm.DEFAULT_MODEL,
    )
```

These two `await` calls must run **sequentially** — you can't run them with `asyncio.gather()` because Step 2 depends on the output of Step 1. Dependencies → sequential. Independent operations → parallel (as in Session 2).

---

## Running the Full Backend

The backend is in `backend/` at the repo root. From there:

```bash
cd backend
source .venv/bin/activate

# You need both keys in backend/.env:
# OPENROUTER_API_KEY=sk-or-...
# TAVILY_API_KEY=tvly-...

uvicorn main:app --reload
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI.

**Test `/ask`:**

```bash
curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What is FastAPI?", "count": 5}'
```

Expected response:

```json
{
  "question": "What is FastAPI?",
  "answer": "FastAPI is a modern Python web framework for building APIs...[1]...",
  "citations": [
    {"number": 1, "title": "FastAPI — Official Docs", "url": "https://fastapi.tiangolo.com"},
    {"number": 2, ...}
  ],
  "model": "deepseek/deepseek-v4-pro"
}
```

**Test `/search`** (just the search layer, no LLM):

```bash
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{"query": "Python async programming", "count": 3}'
```

---

## The LLM Module: `backend/llm/llm.py`

The LLM module assembles the prompt and calls OpenRouter. The key piece is how search results become context for the model:

```python
def _build_user_prompt(question: str, context: list[SearchResult]) -> str:
    lines = ["Search results:\n"]
    for i, result in enumerate(context, start=1):
        lines.append(f"[{i}] Title: {result.title}")
        lines.append(f"    URL: {result.url}")
        if result.description:
            lines.append(f"    {result.description}")
        lines.append("")
    lines.append(f"Question: {question}")
    return "\n".join(lines)
```

The model sees something like:

```
Search results:

[1] Title: FastAPI — Official Docs
    URL: https://fastapi.tiangolo.com
    FastAPI is a modern, fast web framework for building APIs with Python...

[2] Title: FastAPI — Wikipedia
    URL: https://en.wikipedia.org/wiki/FastAPI
    ...

Question: What is FastAPI?
```

This is **grounding**: you give the model current, factual context and instruct it (via the system prompt) to answer only from that context. The numbered format `[1]`, `[2]` matches the inline citations the model writes, which matches the `citations` array we build from the same `results` list. The numbers align end-to-end.

---

## Extension Challenges

### 1. Add `search_depth="advanced"`

Tavily's advanced depth returns more detailed page content at the cost of more credits. Add a query parameter to the `/ask` endpoint:

```python
class AskRequest(BaseModel):
    question: str
    count: int = Field(default=5, ge=1, le=10)
    deep: bool = False   # ← new
```

In the route, pass `depth="advanced" if request.deep else "basic"` to `search()`. Test with a complex research question and compare the answer quality.

### 2. Show elapsed time per stage

Measure how long each step takes and include it in the response:

```python
import time

t0 = time.perf_counter()
results = await search(...)
search_ms = int((time.perf_counter() - t0) * 1000)

t0 = time.perf_counter()
answer = await llm.ask(...)
llm_ms = int((time.perf_counter() - t0) * 1000)
```

Add `search_ms` and `llm_ms` fields to `AskResponse`. What fraction of total time is the LLM vs the search?

### 3. Parallel multi-source search

Run two searches in parallel — one with `search_depth="basic"` and one Tavily "news" topic — then merge and de-duplicate the results before calling the LLM:

```python
basic, news = await asyncio.gather(
    search(client, question, count=3),
    search(client, question, count=2, depth="basic"),  # or use topic="news"
)
combined = {r.url: r for r in basic + news}   # de-dup by URL
results = list(combined.values())
```

---

## What's Next

Session 7 adds **authentication and a database**. Right now, anyone with the URL can call `/ask`. Next session:

- Users sign in with Google via Supabase (OAuth 2.0)
- Every request carries a JWT — the backend verifies it using `python-jose`
- FastAPI's `Depends()` injects the verified user identity into protected routes
- Search history is saved to Postgres and associated with the user's UUID

The search-and-answer pipeline you built this session becomes the core of a multi-user product.
