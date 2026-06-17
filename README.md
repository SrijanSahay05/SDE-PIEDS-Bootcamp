# SDE Bootcamp — PIEDS, BITS Pilani, May–June 2026

A hands-on software engineering bootcamp that builds toward a **full-stack Perplexity clone** — an AI-powered search and answer engine — session by session, starting from Python fundamentals.

---

## The Goal: Build a Perplexity Clone

By the end of the bootcamp, participants will have built a complete web application that mirrors the core of [Perplexity AI](https://www.perplexity.ai):

- A user signs in with Google and types a natural-language question
- The backend searches the web via Brave Search and retrieves relevant sources
- An LLM (via OpenRouter) synthesizes a cited answer and streams it back in real time
- Every search is saved to the user's personal history and searchable by meaning using vector embeddings

Every session introduces one new layer of the stack so the final product is assembled piece by piece rather than handed over at the end.

---

## Tech Stack

### Backend

| Library / Tool | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com) | Async API framework — route handlers, dependency injection, OpenAPI docs |
| uvicorn | ASGI server for running FastAPI |
| httpx | Async HTTP client for calling external APIs |
| Pydantic | Runtime data validation and serialisation |
| asyncpg | Async Postgres driver for database queries |
| python-jose | JWT decoding and verification |
| anthropic | Anthropic Python SDK for agentic scripting |

### Frontend

| Library / Tool | Purpose |
|---|---|
| [Next.js 14](https://nextjs.org) (App Router) | React framework — file-based routing, server components |
| React + TypeScript | Components, hooks, type-safe API contracts |
| Tailwind CSS | Utility-first styling |
| react-markdown | Rendering LLM output as formatted text |
| Supabase JS client | Auth session management and OAuth flow in the browser |

### Database & Infrastructure

| Tool | Purpose |
|---|---|
| [Supabase](https://supabase.com) | Managed Postgres + Auth + Row Level Security |
| [pgvector](https://github.com/pgvector/pgvector) | Vector embeddings stored and queried inside Postgres |
| Docker + Compose | Containerisation and multi-service orchestration |
| GitHub Actions | CI/CD pipelines for automated code review |

### External APIs

| API | Purpose |
|---|---|
| [OpenRouter](https://openrouter.ai) | Single API key for 100+ LLMs — Mistral, GPT-4o, Claude, Llama |
| OpenAI Embeddings (via OpenRouter) | `text-embedding-3-small` for semantic search |
| [Brave Search API](https://brave.com/search/api/) | Web search results (free tier: 2000 queries/month) |

---

## Architecture Overview

```
Browser (Next.js + TypeScript)
        │
        │  HTTPS  (REST + SSE streaming)
        ▼
FastAPI Backend
        │
        ├── Auth middleware  ──────►  Supabase Auth  (Google OAuth 2.0 → JWT)
        │
        ├── /ask pipeline
        │       ├── Semantic cache  ───►  pgvector  (skip LLM if similar query exists)
        │       ├── Brave Search API  (web results)
        │       ├── OpenRouter LLM  (streaming, cited answer)
        │       └── Save to Supabase (chat history + embedding)
        │
        └── Postgres (Supabase)  ──►  users · chats · embeddings
                                       (RLS: users see only their own rows)
```

**Request flow for a single question:**

1. User signs in with Google — Supabase Auth issues a JWT to the browser.
2. Next.js sends the question to `POST /ask` with the JWT in the `Authorization` header.
3. FastAPI validates the JWT, embeds the query, and checks pgvector for a semantically similar cached answer (cosine similarity > 0.92 → return immediately, zero LLM tokens spent).
4. On cache miss: Brave Search fetches live results; OpenRouter streams the LLM answer back via Server-Sent Events (SSE); the completed answer is saved to Supabase with its embedding.
5. Next.js renders the streaming answer and source cards as chunks arrive.

---

## Sessions

| # | Date | Topic | Outcome |
|---|---|---|---|
| 01 | Thu, May 28 | Python fundamentals + dev environment | CLI weather tool using `requests` |
| 02 | Mon, Jun 2 | Python async + HTTP basics | Concurrent fetcher with `httpx` + `asyncio.gather()` |
| 03 | Tue, Jun 3 | APIs — consuming and building | Typed Brave Search wrapper with Pydantic |
| 04 | Thu, Jun 5 | FastAPI backend — project setup | `/search` endpoint with Swagger docs and CORS |
| 05 | Fri, Jun 6 | LLM integration via OpenRouter | `/ask` endpoint with system prompts and cited answers |
| 06 | Thu, Jun 12 | Supabase + Auth (OAuth + JWT) | Google Sign-In, JWT verification via `Depends()` |
| 07 | Fri, Jun 13 | Docker, Postgres, Auth | Docker compose DB setup, DB schemas (Excel analogy), ORMs, Auth concepts |
| 08 | Mon, Jun 16 | TypeScript + Next.js frontend | Search UI with Google login and chat history sidebar |
| 09 | Tue, Jun 17 | Streaming responses + UI | Real-time SSE rendering with `react-markdown` |
| 10 | Thu, Jun 19 | Docker — containerising the app | `docker compose up --build` runs the full stack |
| 11 | Fri, Jun 20 | Agentic scripting + coding agents | Python scripting agent; Claude Code live demo |
| 12 | Mon, Jun 23 | Search integration + RAG basics | Context builder with chunking and relevance scoring |
| 13 | Tue, Jun 24 | Frontend polish + citations UI + chat history | Inline citations, skeleton states, optimistic updates |
| 14 | Thu, Jun 26 | Deployment + environment management | Live app on Railway/Render + Vercel |
| 15 | Bonus | Code review workflows with AI agents | Pre-commit hook + GitHub Actions CI using Claude |

Each session folder contains a `README.md` with setup instructions and a planned-session document under `planned_sessions/`.

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop
- A Supabase project (free tier is sufficient)
- Google OAuth credentials (from Google Cloud Console — enabled in Supabase Auth)
- An [OpenRouter](https://openrouter.ai) API key (free $5 credit on registration)
- A [Brave Search API](https://brave.com/search/api/) key (free tier: 2000 queries/month)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in keys
uvicorn main:app --reload
# API docs → http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local       # fill in NEXT_PUBLIC_SUPABASE_URL etc.
npm run dev
# UI → http://localhost:3000
```

### Full stack with Docker

```bash
cp .env.example .env             # one shared env file at the repo root
docker compose up --build
```

### Database

```bash
# Run SQL in the Supabase dashboard, or apply via CLI:
supabase db push
```

---

## Repository Structure

```
perplexity-clone/
├── README.md
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── search.py            # Brave Search integration
│   ├── llm.py               # OpenRouter integration
│   ├── auth.py              # JWT verification dependency
│   ├── db.py                # Supabase / asyncpg queries
│   ├── models.py            # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main search page
│   │   └── api/ask/         # API route proxy
│   ├── components/
│   │   ├── SearchBar.tsx
│   │   ├── AnswerPanel.tsx
│   │   ├── SourceCard.tsx
│   │   └── ChatHistory.tsx
│   ├── lib/
│   │   └── supabase.ts      # Supabase client
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   └── ai_review.py         # AI code review script (Session 15)
├── .github/
│   └── workflows/
│       └── ai-review.yml
├── supabase/
│   └── schema.sql           # Table definitions + RLS policies
├── docker-compose.yml
├── .env.example             # Template — never commit .env
├── planned_sessions/        # Instructor session design docs
└── session-01/              # Per-session working code and notes
```

---

## Key Concepts by Layer

### FastAPI
- Path operations, dependency injection (`Depends()`), `async def` handlers
- Pydantic models for request/response validation
- CORS middleware, background tasks
- `StreamingResponse` for Server-Sent Events

### LangChain / OpenRouter
- Chat completion format — `messages` array, roles, token limits
- System prompt engineering for grounded, cited answers
- Streaming responses — reading chunks and forwarding via SSE
- Semantic caching — skip the LLM when a similar question was answered recently

### Next.js + TypeScript
- App Router — `app/page.tsx`, server vs client components
- `useState`, `useEffect`, `useRef` hooks
- `ReadableStream` for consuming SSE in the browser
- TypeScript interfaces for API contracts
- Tailwind CSS utility classes

### OAuth 2.0 + Supabase Auth
- Authorization Code Flow — browser → Supabase → Google → back to the app
- JWT structure (header, payload, signature) and verification with `python-jose`
- Bearer token auth — JWT passed on every protected request
- Row Level Security (RLS) — Postgres-enforced per-user data isolation

### pgvector
- `VECTOR(1536)` column type in Postgres
- Embedding generation with `text-embedding-3-small`
- Cosine similarity search using the `<=>` operator
- `ivfflat` index for performant approximate nearest-neighbour queries

### Docker
- `Dockerfile` anatomy — `FROM`, `WORKDIR`, `COPY`, `RUN`, `CMD`
- `docker-compose.yml` for multi-service networking and env passthrough
- `.dockerignore` to keep images lean
- Environment separation — never bake secrets into images

---

## Bootcamp Details

**Institution:** PIEDS, BITS Pilani  
**Duration:** May–June 2026  
**Format:** 14 weekly sessions × 1 hour each (+ 1 bonus session), live coding throughout  
