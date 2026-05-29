# Session 02 — Async HTTP & Concurrency

**Goal:** Understand the difference between synchronous and asynchronous code, benchmark both approaches against a real API, and know exactly when to choose one over the other.

---

## Setup

```bash
# Activate the virtual environment from the project root
source .venv/bin/activate

# Install async dependencies
pip install httpx

# Verify
python3 -c "import httpx; print(httpx.__version__)"
```

---

## Sync vs Async — The Core Idea

### Synchronous (blocking)

Your program does one thing at a time. Each operation must finish before the next one starts.

```python
# time_Weather.py — one city at a time
for city in cities:
    weather = sync_get_weather(city)   # waits for response before moving on
    print(weather)
```

Timeline for 10 cities (each taking ~0.5s):

```
City 1: [====request====]
City 2:                  [====request====]
City 3:                                  [====request====]
...
Total: ~5s
```

### Asynchronous (non-blocking)

Your program fires all requests at once and handles each response as it arrives. While waiting for one server to reply, Python is free to send the next request.

```python
# async_weather.py — all cities in flight simultaneously
results = await asyncio.gather(
    *[get_weather(client, city, sem) for city in CITIES]
)
```

Timeline for 10 cities:

```
City 1:  [====request====]
City 2:  [====request====]
City 3:  [====request====]
...
Total: ~0.5s  (same wall-clock time as a single request)
```

---

## Key Async Concepts

### `async def` and `await`

`async def` declares a coroutine — a function that can pause without blocking the entire program.

`await` is the pause point. It suspends the current coroutine and yields control back to the event loop so other work can run.

```python
async def get_weather(client: httpx.AsyncClient, city: str) -> str:
    response = await client.get(f"https://wttr.in/{city}", timeout=10)
    #           ^^^^^ pauses here — event loop runs other coroutines
    response.raise_for_status()
    return response.text.strip()
```

Rule: you can only use `await` inside an `async def`. An `async def` function must itself be awaited (or handed to the event loop via `asyncio.run()`).

### `asyncio.gather()` — run coroutines concurrently

`gather()` takes any number of coroutines, starts them all, and returns their results in order once all finish.

```python
results = await asyncio.gather(
    *[get_weather(client, city, sem) for city in CITIES],
    return_exceptions=True,   # don't let one failure cancel the rest
)
```

`return_exceptions=True` means a failed request comes back as an `Exception` object instead of crashing the whole gather. Always use it when fetching a list.

### `asyncio.Semaphore` — rate limiting

A Semaphore limits how many coroutines can be inside a block simultaneously. Without it, `gather()` would open hundreds of connections at once — most servers will rate-limit or block you.

```python
sem = asyncio.Semaphore(10)   # at most 10 requests in flight at once

async def get_weather(client, city, sem):
    async with sem:            # acquires a "slot"; releases it when the block exits
        response = await client.get(...)
```

### `httpx.AsyncClient` — the async HTTP client

`httpx` is a drop-in upgrade from `requests` with full async support. Use it as a context manager so the underlying connection pool is cleaned up properly.

```python
async with httpx.AsyncClient() as client:
    results = await asyncio.gather(...)
# connection pool is closed here automatically
```

The `async with` syntax is the async equivalent of `with` — it calls `__aenter__` and `__aexit__` asynchronously.

### `asyncio.run()` — entry point

`asyncio.run()` creates an event loop, runs the given coroutine to completion, then tears the loop down. It is the standard top-level entry point for any async program.

```python
asyncio.run(main())
```

Never call `asyncio.run()` inside an already-running event loop (e.g. inside another coroutine). Call it exactly once, at the bottom of your script.

---

## When to Use Sync vs Async

The deciding factor is whether your bottleneck is **waiting** (I/O-bound) or **computing** (CPU-bound).

### Use async when:

| Scenario | Why |
|---|---|
| Fetching data from multiple URLs | Requests sit idle waiting for the server — async fills that idle time with other requests |
| Polling many APIs in parallel | Same reason — network latency dominates |
| Web servers handling many simultaneous clients | Each request waits on DB/network; async lets one thread serve thousands |
| Reading/writing many files concurrently | Disk I/O has the same wait-and-resume pattern |

Async shines whenever your program spends most of its time *waiting* for something external to respond.

### Use sync when:

| Scenario | Why |
|---|---|
| Database transactions (ACID) | See below — correctness requires strict ordering |
| CPU-heavy work (image processing, ML inference) | Async doesn't help — Python is busy computing, not waiting |
| Scripts that do one thing sequentially | Async overhead isn't worth the complexity |
| Code that calls sync-only libraries | Mixing sync blocking calls into async code stalls the event loop |

---

## ACID Transactions — A Case for Sync

**ACID** stands for Atomicity, Consistency, Isolation, Durability. These are the four guarantees a database gives you for a transaction.

| Property | Meaning |
|---|---|
| **Atomicity** | All steps in the transaction succeed, or none of them do. No partial writes. |
| **Consistency** | The database moves from one valid state to another. Rules (constraints, foreign keys) are never violated. |
| **Isolation** | Concurrent transactions don't interfere with each other. Each sees a consistent snapshot. |
| **Durability** | Once committed, data survives crashes, power loss, etc. |

### Why ACID transactions should be synchronous

Consider a bank transfer — debit one account, credit another:

```python
# WRONG — async with no transaction
async def transfer(from_id, to_id, amount):
    await db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, from_id)
    # << if a crash or error happens here, money has left but not arrived
    await db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, to_id)
```

Async here is dangerous. Between the two `await` points, the event loop can suspend this coroutine and run something else — including *another transfer*. If anything fails between the two statements, you have an inconsistent database: money is gone from one account but never reached the other.

The correct approach wraps both writes in a single atomic transaction:

```python
# CORRECT — sync, inside a single transaction
def transfer(conn, from_id: int, to_id: int, amount: float) -> None:
    with conn.begin():   # starts a transaction
        conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, from_id)
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, to_id)
    # commit happens here — both writes land atomically, or neither does
```

**The rule:** whenever the correctness of an operation depends on multiple steps all succeeding together, use a synchronous transaction. The ordering and atomicity guarantees of ACID are incompatible with the "fire and interleave" model of async.

Other real-world examples where sync + transactions win over async:
- Inventory reservation (check stock, decrement count, create order)
- Double-entry bookkeeping
- User registration (insert user row, create default settings row, send welcome email via queue — all or nothing)

---

## Benchmarking — `time.perf_counter()`

`time.perf_counter()` returns a high-resolution timer (in fractional seconds). Take a snapshot before and after the work, then subtract.

```python
import time

start = time.perf_counter()
# ... do work ...
elapsed = time.perf_counter() - start
print(f"Done in {elapsed:.2f}s")
```

Use `perf_counter` (not `time.time()`) for measuring short durations — it has much higher resolution and is not affected by system clock adjustments.

---

## Walking Through the Scripts

### `time_Weather.py` — sync baseline

Calls each city sequentially using `requests`. Measures total elapsed time so you can see the cumulative cost of blocking I/O.

```python
start = time.perf_counter()
for city in cities:
    weather = sync_get_weather(city)   # blocks until response arrives
    print(weather)
print(f"{time.perf_counter() - start:.2f}s")
```

### `async_weather.py` — async with semaphore

Fires all requests concurrently via `asyncio.gather()`, capped at 10 simultaneous connections by a `Semaphore`. Measures the same wall-clock time to show the speedup.

```python
sem = asyncio.Semaphore(10)

async def main() -> None:
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[get_weather(client, city, sem) for city in CITIES],
            return_exceptions=True,
        )
    print(f"Fetched {len(CITIES)} cities in {time.perf_counter() - start:.2f}s")
```

On a typical connection, the sync version takes ~5–8s for 10 cities; the async version takes ~0.5–1s.

---

## Extension Challenges

### 1. Add error handling per city

`return_exceptions=True` returns exceptions as values. Print a clear message for each failed city instead of crashing.

```python
for city, result in zip(CITIES, results):
    if isinstance(result, Exception):
        print(f"{city}: failed — {result}")
    else:
        print(result)
```

### 2. Try different semaphore limits

Change `asyncio.Semaphore(10)` to `3`, `5`, or `20`. Observe how the time changes. At very high limits servers may start returning `429 Too Many Requests`.

### 3. Add a retry for transient failures

```python
async def get_weather_with_retry(client, city, sem, retries=3):
    for attempt in range(retries):
        try:
            return await get_weather(client, city, sem)
        except Exception:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(0.5 * (attempt + 1))   # exponential backoff
```

### 4. Extend to JSON APIs

`httpx` parses JSON the same way `requests` does:

```python
async def get_github_user(client: httpx.AsyncClient, username: str) -> dict:
    response = await client.get(f"https://api.github.com/users/{username}", timeout=10)
    response.raise_for_status()
    return response.json()
```

Fetch multiple GitHub profiles concurrently and compare follower counts.

---

## What's Next

Session 3 introduces **data persistence** — writing results to files and databases so your program's output survives between runs.
