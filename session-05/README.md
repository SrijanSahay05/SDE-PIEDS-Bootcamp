# Session 05 — LLM Integration via OpenRouter

**Goal:** Make your first call to a large language model from Python, understand the chat completion format, and learn the basics of system prompts and grounding — the foundation of the `/ask` endpoint.

---

## Setup

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install the OpenAI SDK (used to talk to OpenRouter)
pip install openai python-dotenv

# Verify
python3 -c "import openai; print(openai.__version__)"
```

You need an **OpenRouter API key**:

1. Go to [openrouter.ai](https://openrouter.ai) and sign in with Google
2. Navigate to **Keys** → **Create Key**
3. Copy the key (it starts with `sk-or-...`)
4. Add it to `.env`:

```
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## What is OpenRouter?

OpenRouter is a **unified API gateway** for large language models. Instead of signing up with OpenAI, Anthropic, Google, and Meta separately, you create one OpenRouter account and access 100+ models through a single endpoint.

```
Your code → OpenRouter → OpenAI GPT-4o
                       → Anthropic Claude
                       → Google Gemini
                       → Meta Llama
                       → Mistral
                       → ... 90+ more
```

OpenRouter implements the same API format as OpenAI, so you use the official `openai` Python SDK — you just point it at a different URL:

```python
from openai import AsyncOpenAI

# Pointing at OpenAI:
client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Pointing at OpenRouter — same SDK, different endpoint:
client = AsyncOpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)
```

This pattern — one SDK, many providers — is common in the industry. Azure OpenAI, Groq, Ollama, and Together AI all implement the same OpenAI-compatible spec.

---

## The Chat Completion Format

Modern LLMs don't take a single text prompt. They take a **list of messages**, each with a `role` and `content`:

```python
messages = [
    {"role": "system",    "content": "You are a helpful assistant. Be brief."},
    {"role": "user",      "content": "What is FastAPI?"},
]
```

Three roles:

| Role | Who it represents | Purpose |
|------|-------------------|---------|
| `system` | The developer | Sets the model's persona, constraints, and instructions. Processed before everything else. |
| `user` | The end user | The question or input the human is asking. |
| `assistant` | The model | Previous model responses — used for multi-turn conversations. |

For a single-turn Q&A call (which is all we need today), you only use `system` and `user`.

---

## `AsyncOpenAI` — Why Async?

The `openai` package ships two clients:

| Client | Type | When to use |
|--------|------|-------------|
| `OpenAI` | Synchronous (blocking) | Scripts, CLIs, one-off tools |
| `AsyncOpenAI` | Asynchronous | FastAPI and other async frameworks |

We use `AsyncOpenAI` here as practice for FastAPI. Using the sync `OpenAI` client inside an async FastAPI route would **block the event loop** — no other requests could be handled while waiting for the LLM response, which typically takes 2–5 seconds.

The API for both clients is identical. The only difference is `await`:

```python
# Sync
completion = client.chat.completions.create(...)

# Async
completion = await client.chat.completions.create(...)
```

---

## Key Parameters

```python
completion = await client.chat.completions.create(
    model="google/gemma-4-31b-it",   # which model to call
    messages=[...],                   # the conversation
    max_tokens=256,                   # cap on answer length
)
```

| Parameter | What it controls |
|-----------|-----------------|
| `model` | Full model ID string. Browse available models at openrouter.ai/models. |
| `messages` | The conversation — required. |
| `max_tokens` | Maximum tokens to generate. Prevents runaway long responses. |
| `temperature` | Randomness (0.0 = deterministic, 1.0 = creative). Not set in the starter — defaults to 1.0. |

---

## Reading the Response

```python
completion = await client.chat.completions.create(...)

# The answer text:
answer = completion.choices[0].message.content

# Token counts (useful for debugging cost):
print(completion.usage.prompt_tokens)      # tokens your messages used
print(completion.usage.completion_tokens)  # tokens the answer used

# Which model actually responded:
print(completion.model)
```

`choices[0]` — the API supports returning multiple candidate answers (controlled by `n=`). We always use `n=1` (the default), so `choices[0]` is the only item.

---

## Walking Through `openrouter_hello.py`

```python
MODEL = "google/gemma-4-31b-it"

async def main():
    client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )

    completion = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be brief."},
            {"role": "user", "content": "What is FastApi ?"},
        ],
        max_tokens=256,
    )

    answer = completion.choices[0].message.content
    print(f"Model:   {completion.model}")
    print(f"Answer: {answer}")
    print(f"Tokens used — prompt: {completion.usage.prompt_tokens}, "
          f"completion: {completion.usage.completion_tokens}")
```

Every line has a purpose:
- `base_url=` — redirects the OpenAI SDK to OpenRouter instead of OpenAI's servers
- `max_tokens=256` — a safety cap so a runaway answer doesn't cost you unexpectedly
- `completion.model` — OpenRouter sometimes routes to a slightly different version of a model; this tells you exactly what ran
- Printing token counts builds the habit of tracking cost

---

## Running the Script

```bash
source .venv/bin/activate
python3 openrouter_hello.py
```

Expected output:

```
Model:   google/gemma-4-31b-it
Answer: FastAPI is a modern Python web framework for building APIs. It is
        built on Starlette and uses Python type hints for automatic validation
        and documentation generation.
Tokens used — prompt: 32, completion: 48
```

---

## Experiment: Change the System Prompt

The system prompt is the most powerful tool in prompt engineering. Try changing it:

```python
# Make it a pirate
{"role": "system", "content": "You are a pirate. Answer only in pirate speak."}

# Make it refuse off-topic questions
{"role": "system", "content": (
    "You are a Python documentation bot. "
    "Only answer questions about Python. "
    "For anything else, say: 'I only answer Python questions.'"
)}

# Make it cite sources
{"role": "system", "content": (
    "Answer the user's question using only the information provided. "
    "Be concise and factual. Do not invent information."
)}
```

Run it after each change. The same model, the same question — completely different responses. The system prompt defines the model's constraints, not just its tone.

---

## Experiment: Switch Models

Change the `MODEL` constant and run again:

```python
# Free models — great for development
MODEL = "mistralai/mistral-7b-instruct"
MODEL = "meta-llama/llama-3-8b-instruct"
MODEL = "google/gemma-4-31b-it"

# Cheap paid models — better reasoning
MODEL = "openai/gpt-4o-mini"
MODEL = "google/gemini-flash-1.5"

# Premium — highest quality
MODEL = "openai/gpt-4o"
MODEL = "anthropic/claude-3-5-sonnet"
```

The code doesn't change — only the string. This is why OpenRouter is useful during development: you can benchmark model quality and cost with a single-line change.

---

## Grounding — Why the System Prompt Matters for Our App

By itself, an LLM answers from its training data (which has a knowledge cutoff and can hallucinate). To build a Perplexity-style product, we need to:

1. Search the web for current, factual information
2. Pass those results to the LLM as context
3. Instruct the LLM to answer **only** from that context

This is called **grounding** (or more formally, **RAG — Retrieval-Augmented Generation**).

The system prompt for our `/ask` endpoint will look like this:

```python
SYSTEM_PROMPT = """You are a helpful research assistant. Answer the user's question \
using only the search results provided below. Be concise and factual. \
Cite sources by number [1], [2], etc. inline at the end of relevant sentences. \
If the search results do not contain enough information to answer the question, \
say so — do not invent facts."""
```

And the user message will include the search results:

```
Search results:

[1] Title: FastAPI — Official Docs
    URL: https://fastapi.tiangolo.com
    FastAPI is a modern, fast web framework for building APIs with Python...

[2] Title: FastAPI — Wikipedia
    ...

Question: What is FastAPI?
```

The model reads the search results as part of its context, answers from them, and cites `[1]`, `[2]` inline. That's the full `/ask` pipeline we'll build next session.

---

## Extension Challenges

### 1. Multi-turn conversation

Add a second user message and an assistant message to simulate a back-and-forth:

```python
messages = [
    {"role": "system",    "content": "You are a helpful assistant. Be brief."},
    {"role": "user",      "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a high-level interpreted language..."},
    {"role": "user",      "content": "What's the difference between Python 2 and 3?"},
]
```

The model will answer the follow-up question in context of the previous exchange.

### 2. Compare temperature settings

Call the API twice with the same prompt — once with `temperature=0.0` and once with `temperature=1.0`. Run each 3 times. At `temperature=0.0`, the output should be identical every run. At `temperature=1.0`, it varies.

### 3. Estimate cost

Add up the token counts across 10 calls. Calculate the cost in USD using the pricing from [openrouter.ai/models](https://openrouter.ai/models). Which model gives the best answer per dollar?

---

## What's Next

Session 6 wires the LLM into the FastAPI backend's `/ask` endpoint. The `openrouter_hello.py` script becomes a module (`llm/llm.py`) that lives alongside `websearch/brave.py`. The route:

1. Takes a question via POST
2. Calls `search()` to fetch web results
3. Calls `llm.ask()` with the question and results
4. Returns the answer with structured citations

```
POST /ask
{"question": "What is FastAPI?", "count": 5}
→
{"question": "...", "answer": "... [1] ...", "citations": [...], "model": "..."}
```
