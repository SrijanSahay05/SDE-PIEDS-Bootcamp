# Backend — FastAPI Search & Answer Server

The running backend for the Perplexity clone. This is the accumulated result of Sessions 4–6: a FastAPI server that takes a natural-language question, searches the web via Tavily, sends the results to an LLM via OpenRouter, and returns a cited answer.

---

## What It Does

Two endpoints:

| Endpoint | What it does |
|----------|-------------|
| `POST /search` | Takes a query, calls Tavily, returns a list of web results |
| `POST /ask` | Takes a question, calls Tavily then an LLM, returns a cited answer |
| `GET /health` | Returns `{"status": "ok"}` — useful for liveness checks |

The `/ask` pipeline is the core:

```
POST /ask {"question": "What is FastAPI?", "count": 5}

→ Tavily Search: fetch top 5 results for the question
→ Build a numbered context block for the LLM
→ OpenRouter LLM: generate a cited answer from those results
→ Build a structured citations list from the same results

Response:
{
  "question": "What is FastAPI?",
  "answer": "FastAPI is a modern Python web framework [1]. It was created by
             Sebastián Ramírez and is built on Starlette and Pydantic [2]...",
  "citations": [
    {"number": 1, "title": "FastAPI Docs", "url": "https://fastapi.tiangolo.com"},
    {"number": 2, ...}
  ],
  "model": "deepseek/deepseek-v4-pro"
}
```

---

## Setup

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn httpx "python-dotenv" openai "tavily-python" pydantic

# Create your .env file
cp .env.example .env   # if it exists, or create manually
```

Add these keys to `backend/.env`:

```
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- **OpenRouter key**: [openrouter.ai](https://openrouter.ai) → sign in → Keys → Create Key
- **Tavily key**: [app.tavily.com](https://app.tavily.com) → sign in → shown on dashboard (free tier: 1,000/month)

---

## Running the Server

```bash
# From the backend/ directory, with .venv active:
uvicorn main:app --reload
```

- API: [http://localhost:8000](http://localhost:8000)
- Interactive docs (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

`--reload` makes the server restart automatically when you save a file. Use it during development; leave it out in production.

---

## File Structure

```
backend/
├── main.py              # FastAPI app — routes, models, lifespan, CORS
├── llm/
│   ├── __init__.py
│   └── llm.py           # OpenRouter wrapper — ask() function + prompt assembly
├── websearch/
│   ├── __init__.py
│   ├── brave.py         # Brave Search wrapper (from Session 3)
│   └── tavily_search.py # Tavily wrapper (current default)
└── .venv/
```

Each module has one responsibility:
- `websearch/` — knows how to talk to search APIs, returns `list[SearchResult]`
- `llm/` — knows how to talk to OpenRouter, takes a question + context, returns an answer string
- `main.py` — wires them together into HTTP routes, manages shared clients

Neither `websearch/` nor `llm/` imports from FastAPI. They're plain async Python modules — usable in scripts, tests, or any other framework.

---

## Key Design: Shared Clients via `lifespan`

Creating a new HTTP client or LLM client on every request is expensive — each call would open a new TCP connection. Instead, the app creates all clients once at startup and stores them on `app.state`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts
    app.state.http_client = httpx.AsyncClient()
    app.state.llm_client = AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
    )
    app.state.tavily_client = AsyncTavilyClient(
        api_key=os.environ.get("TAVILY_API_KEY", "")
    )
    yield
    # Runs once when the server stops
    await app.state.http_client.aclose()
    await app.state.llm_client.close()
```

Routes read from `app.state`:

```python
@app.post("/ask")
async def ask_endpoint(request: AskRequest):
    tavily_client = app.state.tavily_client   # shared, not new
    llm_client = app.state.llm_client         # shared, not new
    ...
```

---

## Key Design: Sequential Awaits in `/ask`

The `/ask` route makes two external API calls. They must run in sequence — the LLM call needs the search results as input:

```python
# Step 1: get search results
results = await search(tavily_client, request.question, request.count)

# Step 2: generate the answer using those results
answer = await llm.ask(
    client=llm_client,
    question=request.question,
    context=results,   # depends on Step 1
)
```

This is different from Session 2's `asyncio.gather()`. There, the requests were independent. Here, the second call depends on the first output. Dependencies → sequential. Independent → parallel.

---

## Pydantic Request & Response Models

All inputs and outputs are typed Pydantic models. FastAPI uses these to:
- Validate incoming request bodies (return `422` if invalid)
- Document the API in Swagger UI automatically
- Serialize response objects to JSON

```python
class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    count: int = Field(default=5, ge=1, le=10)

class Citation(BaseModel):
    number: int
    title: str
    url: str

class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    model: str
```

`Field(...)` — the `...` means required (no default). `min_length=5` enforces minimum length. `ge=1, le=10` enforces numeric bounds. FastAPI runs these validators before your route function even runs.

---

## The LLM Prompt

`llm/llm.py` assembles the system and user prompts. The system prompt instructs the model to stay grounded in the provided sources:

```python
SYSTEM_PROMPT = """You are a helpful research assistant. Answer the user's question \
using only the search results provided below. Be concise and factual. \
Cite sources by number [1], [2], etc. inline at the end of relevant sentences. \
If the search results do not contain enough information to answer the question, \
say so — do not invent facts."""
```

The user message is a numbered list of search results followed by the question:

```
Search results:

[1] Title: FastAPI — Official Docs
    URL: https://fastapi.tiangolo.com
    FastAPI is a modern, fast web framework for building APIs with Python...

[2] ...

Question: What is FastAPI?
```

The numbered format matches the inline citations `[1]`, `[2]` the model writes in its answer, which matches the `citations` array built from the same `results` list — so the numbers align end-to-end between the LLM answer and the structured citation data.

---

## CORS Configuration

The `CORSMiddleware` allows the Next.js frontend (running on port 3000) to call the backend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Without this, browsers block cross-origin requests by default. CORS is a browser security mechanism — tools like `curl` and the Swagger UI are not affected by it.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `OPENROUTER_API_KEY` not set | Missing from `.env` | Add key to `backend/.env` |
| `TAVILY_API_KEY` not set | Missing from `.env` | Add key to `backend/.env` |
| `422 Unprocessable Entity` | Request body doesn't match the model | Check `question` is ≥5 chars, `count` is 1–10 |
| `500 Invalid Brave API key` | Endpoint called a Brave route (unused) | Backend uses Tavily now — ignore if `/ask` works |
| `504 Gateway Timeout` | Tavily or OpenRouter took too long | Retry; or reduce `count` to limit context size |
| `429` on `/ask` | Rate limit on Tavily (1,000/month) or OpenRouter | Wait or switch to a different model |
| `ModuleNotFoundError` | venv not activated | Run `source .venv/bin/activate` |
| `uvicorn: command not found` | uvicorn not installed | `pip install uvicorn` |

---

## What's Coming Next

Session 7 focuses on Docker, Databases, and Authentication:

- **Docker & DBs**: Setting up a PostgreSQL 17 database using `docker-compose`. We compare relational vs non-relational databases, and explore in-memory DBs like Redis for caching.
- **Mental Model**: Understanding schemas, tables, and records through a Microsoft Excel analogy.
- **Auth & ORMs**: Planning the request structure for register/login endpoints. We also introduce Object Relational Mapping (ORM) to replace raw SQL queries, setting the stage for defining a User schema and securing our `/ask` endpoint.

The `main.py` will soon grow to incorporate these persistent storage and authentication layers.
