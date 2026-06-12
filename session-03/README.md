# Session 03 — Typed API Wrappers with Pydantic

**Goal:** Replace raw dict access with typed Pydantic models when calling external APIs, and build a reusable async search module that becomes the `websearch` layer of the FastAPI backend.

---

## Setup

```bash
# Activate the virtual environment from the project root
source .venv/bin/activate

# Install this session's dependencies
pip install httpx pydantic python-dotenv

# Verify
python3 -c "import httpx, pydantic; print(httpx.__version__, pydantic.__version__)"
```

You also need a **Brave Search API key**:

1. Go to [brave.com/search/api](https://brave.com/search/api/)
2. Sign up → Dashboard → **Add Subscription** → choose **Free** (2,000 queries/month, no card required)
3. Copy the key and add it to a `.env` file in this directory:

```
BRAVE_API_KEY=BSAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Why Pydantic?

When an API returns JSON, you get a raw Python `dict`. You have no guarantees about which keys exist, what types the values are, or whether a field is optional. Bugs hide until runtime.

```python
# Raw dict — no guarantees, no autocomplete
result = response.json()
title = result["web"]["results"][0]["title"]   # KeyError if any key is missing
url   = result["web"]["results"][0]["url"]     # AttributeError if type is wrong
```

Pydantic models declare the shape of data you expect. They validate at the boundary (when you call `.model_validate()`), converting JSON into typed Python objects.

```python
from pydantic import BaseModel
from typing import Optional

class SearchResult(BaseModel):
    title: str
    url: str
    description: Optional[str] = None   # present in some results, absent in others

class WebResults(BaseModel):
    results: list[SearchResult]

class BraveSearchResponse(BaseModel):
    web: WebResults

# Validated at the boundary — raises ValidationError if the shape is wrong
parsed = BraveSearchResponse.model_validate(response.json())

# From here, everything is typed
for result in parsed.web.results:
    print(result.title)   # IDE knows this is a str
    print(result.url)     # IDE knows this is a str
```

If the API response doesn't match your model (wrong type, required field missing), Pydantic raises a clear `ValidationError` immediately — instead of a cryptic `KeyError` or `AttributeError` three function calls later.

---

## Key Concept: `Optional[str] = None`

Some fields exist in some API responses and not others. `Optional[str] = None` tells Pydantic: "this field might not be present — use `None` as the default instead of failing".

```python
description: Optional[str] = None
age: Optional[str] = None
```

Without `= None`, a missing field is a validation error. With it, a missing field silently becomes `None` — which you can check before using.

---

## How `model_validate()` Fits In

`model_validate()` is the Pydantic v2 method for parsing a dict into a model. It:

1. Checks that every required field exists
2. Converts values to the declared type (e.g. a float to int if needed)
3. Runs any custom validators you write
4. Raises `ValidationError` with a precise list of what's wrong if it fails

```python
try:
    parsed = BraveSearchResponse.model_validate(response.json())
except ValidationError as e:
    raise ValueError(f"Unexpected API response shape: {e}") from e
```

Always wrap this in a try/except in production code — APIs change their response format without warning, and you want a clear error message when they do.

---

## Files in This Session

### `step1_raw_request.py` — the starting point

This is what you write first: define the Pydantic models, write the `search()` function, and get it working. The error handling is minimal; the goal is to see the models in action.

Key line to notice:

```python
parsed = BraveSearchResponse.model_validate(response.json())
return parsed.web.results
```

Two lines replace the entire nested dict-unpacking chain. From here, callers work with a `list[SearchResult]` — typed, documented, IDE-completable.

### `step1.py` — cleaner iteration

Same logic, slightly refactored. Error messages are improved and the code is a bit closer to what goes into `brave_search.py`. Compare the two to see how small iterative improvements add up.

### `brave_search.py` — the final module

The production-quality version. The differences from the earlier files are:

**Accepts a query from the command line:**

```python
query = sys.argv[1] if len(sys.argv) > 1 else "what is FastAPI"
```

Instead of hardcoding the query, `sys.argv[1]` reads the first argument you pass when running the script. If you don't pass one, it uses a default. This is the standard pattern for command-line tools.

**Times the request:**

```python
start = time.perf_counter()
results = await search(client, query)
elapsed = time.perf_counter() - start
print(f"Fetched {len(results)} results in {elapsed:.2f}s")
```

`time.perf_counter()` gives a high-resolution timer — more precise than `time.time()` for measuring short durations.

**Granular error handling per status code:**

```python
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        print("Error: Invalid API key. Check your BRAVE_API_KEY in .env")
    elif e.response.status_code == 429:
        print("Error: Rate limit exceeded. Wait a moment and retry.")
    else:
        print(f"HTTP error {e.response.status_code}: {e}")
```

A 401 and a 429 need different responses from the user. Separate branches make the error actionable instead of cryptic.

**Accepts `offset` for pagination:**

```python
async def search(
    client: httpx.AsyncClient,
    query: str,
    count: int = 5,
    offset: int = 0,     # page 2 = offset 5, page 3 = offset 10
) -> list[SearchResult]:
```

Page through results without changing your main logic. The FastAPI backend doesn't use this yet, but the parameter is there for when it does.

---

## Running the Module

```bash
# Activate venv first
source .venv/bin/activate

# Basic usage — uses default query
python3 brave_search.py

# Custom query
python3 brave_search.py "what is async python"
python3 brave_search.py "FastAPI vs Flask"

# Expected output
[1] FastAPI - Modern, fast web framework for building APIs
    URL: https://fastapi.tiangolo.com
    FastAPI is a modern, fast web framework for building APIs with Python...

[2] ...

Fetched 5 results in 0.41s
```

---

## The Module Pattern

Notice that `search()` takes an `httpx.AsyncClient` as its first argument instead of creating one internally:

```python
async def search(
    client: httpx.AsyncClient,   # caller provides the client
    query: str,
    count: int = 5,
) -> list[SearchResult]:
```

This is deliberate. Creating a new client per call means a new TCP connection per call — slow and wasteful. When we plug this into FastAPI, we'll create one shared client at startup and pass it to every function. The module itself stays framework-agnostic; it works in a script, a test, or a server.

---

## Break Things Intentionally

### 1. Use a wrong API key

Change `BRAVE_API_KEY` in your `.env` to something invalid, then run:

```bash
python3 brave_search.py "test"
# Error: Invalid API key. Check your BRAVE_API_KEY in .env
```

Without the specific error check, you'd get a raw `httpx.HTTPStatusError` with a confusing message. The 401 check turns it into an actionable message.

### 2. Remove `response.raise_for_status()`

Comment out this line in `search()`, then use a bad key. The response object will exist, `response.json()` might return something, but Pydantic will either fail to validate or you'll get empty results. `raise_for_status()` ensures you fail loudly the moment the server signals an error.

### 3. Break the Pydantic model

Change `title: str` to `title: int`. Run it. Pydantic will raise a `ValidationError` because the API returns strings, not integers. This is the type safety in action — a mismatch is caught at the boundary.

---

## Extension Challenges

### 1. Fetch multiple queries concurrently

Use `asyncio.gather()` from Session 2 to search for several queries at once:

```python
queries = ["Python async", "FastAPI tutorial", "Pydantic v2"]

async with httpx.AsyncClient() as client:
    all_results = await asyncio.gather(
        *[search(client, q) for q in queries]
    )

for query, results in zip(queries, all_results):
    print(f"\n--- {query} ---")
    print_results(results)
```

Notice that a single `AsyncClient` is shared across all three calls.

### 2. Add a `language` parameter

The Brave Search API accepts a `country` query parameter (`US`, `IN`, `GB`, etc.) that filters results by region. Extend `search()` to accept an optional `country: str = "IN"` parameter and pass it to the API.

### 3. De-duplicate results

Sometimes the same URL appears in multiple results. Write a function that takes `list[SearchResult]` and returns a new list with duplicate URLs removed, preserving the original order.

---

## What's Next

Session 4 wraps this module inside a **FastAPI** route. Instead of calling `search()` from a script, you'll call it from an HTTP handler that any client can reach:

```
POST http://localhost:8000/search
Body: {"query": "what is FastAPI", "count": 5}

Response:
{
  "query": "what is FastAPI",
  "results": [{"title": "...", "url": "...", "description": "..."}],
  "count": 5
}
```

The `search()` function you wrote here goes into `backend/websearch/brave.py` — unchanged. FastAPI provides the HTTP wrapper; this module provides the search logic.
