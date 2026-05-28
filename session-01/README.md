# Session 01 — Python Fundamentals & HTTP

**Goal:** Build a working command-line weather tool that calls a real API, understand how HTTP works, and write clean, typed Python from the start.

---

## Setup

Every project gets its own isolated Python environment so dependencies don't bleed between projects.

**macOS / Linux** (Terminal):
```bash
# Create a virtual environment in this folder
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install the only dependency
pip install requests

# Verify it worked
python3 -c "import requests; print(requests.__version__)"
```

**Windows** (Command Prompt or PowerShell):
```bat
:: Create a virtual environment in this folder
python -m venv .venv

:: Activate it
.venv\Scripts\activate

:: Install the only dependency
pip install requests

:: Verify it worked
python -c "import requests; print(requests.__version__)"
```

> **Windows note:** Use `python` and `pip` (not `python3`). If `python` isn't found, open the Microsoft Store and install Python from there, or re-run the Python installer and check "Add Python to PATH".

Your terminal prompt will show `(.venv)` while the environment is active. Always activate before running any session code.

To deactivate: `deactivate` (same on all platforms)

---

## Core Python Concepts

See `hello_world.py` for live examples of everything below.

### Functions, type hints, and default parameters

```python
# `name: str` and `-> str` are type hints — advisory documentation.
# Python does NOT enforce them at runtime, but editors and mypy do.
def greet(name: str) -> str:
    return f"Hello, {name}"

# Default parameter — callers can omit `greeting`
def greet(name: str, greeting: str = "Hello") -> None:
    print(f"{greeting}, {name}")

greet("Rahul")            # Hello, Rahul   (uses default)
greet("Srijan", "Hi")    # Hi, Srijan
```

### String methods cheatsheet

| Method | What it does | Example |
|---|---|---|
| `.strip()` | Remove leading/trailing whitespace | `"  hi  ".strip()` → `"hi"` |
| `.lower()` | Convert to lowercase | `"Mumbai".lower()` → `"mumbai"` |
| `.upper()` | Convert to uppercase | `"Mumbai".upper()` → `"MUMBAI"` |
| Chaining | Methods return new strings, so you can chain | `"  Mumbai  ".strip().upper()` → `"MUMBAI"` |

```python
city = "   Mumbai   "
city.strip()         # 'Mumbai'
city.strip().upper() # 'MUMBAI'
```

### Conditionals

`if` / `elif` / `else` let your program make decisions.

```python
temperature = 38

if temperature > 35:
    print("Very hot")
elif temperature > 25:
    print("Warm")
else:
    print("Cool")
```

**Comparison operators:**

| Operator | Meaning | Example |
|---|---|---|
| `==` | equal to | `city == "Mumbai"` |
| `!=` | not equal to | `city != ""` |
| `>` / `<` | greater / less than | `temp > 35` |
| `>=` / `<=` | greater or equal / less or equal | `temp >= 35` |

**Logical operators** combine conditions:

```python
if temp > 30 and humidity > 80:
    print("Hot and humid")

if city == "Mumbai" or city == "Chennai":
    print("Coastal city")

if not city:        # empty string is falsy — same as `city == ""`
    print("No city entered.")
```

**Truthiness** — Python treats these as `False` without needing `== False`:
- Empty string `""`
- Zero `0`
- Empty list `[]`
- `None`

Everything else is truthy. So `if not city:` is the idiomatic way to check for empty input.

---

### Loops

#### `for` loop — iterate over a sequence

```python
cities = ["Mumbai", "Delhi", "Bengaluru"]

for city in cities:
    print(city)
# Mumbai
# Delhi
# Bengaluru
```

Use `range()` to repeat something a fixed number of times:

```python
for i in range(3):
    print(i)
# 0
# 1
# 2
```

#### `while` loop — repeat until a condition becomes false

```python
count = 0
while count < 3:
    print(count)
    count += 1
# 0
# 1
# 2
```

#### `break` and `continue`

```python
# break exits the loop immediately
while True:
    city = input("Enter a city (or 'quit'): ").strip()
    if city.lower() == "quit":
        break               # stop the loop
    print(get_weather(city))

# continue skips the rest of this iteration and goes to the next
for city in cities:
    if not city:
        continue            # skip empty strings, keep looping
    print(get_weather(city))
```

Both `break` and `continue` appear in the extension challenges — `break` powers the interactive quit, `continue` skips bad input.

---

## How HTTP Works

Every time your script (or browser) fetches data from the internet, it follows this pattern:

```
Your script                          Server (e.g. wttr.in)
    |                                        |
    |  --- HTTP Request (GET /London) --->   |
    |                                        |  looks up data
    |  <-- HTTP Response (200 OK + body) --  |
    |                                        |
```

### HTTP methods — the "verb" of a request

| Method | Purpose | Real-world example |
|---|---|---|
| `GET` | Fetch/read data | Load a webpage, get weather |
| `POST` | Send new data to create something | Submit a form, send a message |
| `PUT` | Replace a resource entirely | Overwrite a full user profile |
| `PATCH` | Partially update a resource | Change just your email address |
| `DELETE` | Remove a resource | Delete an account |

Weather fetching always uses `GET` — we're only reading, never writing.

### Status codes — the server's reply

| Code | Meaning | What to do |
|---|---|---|
| `200` | OK | All good, use the response |
| `400` | Bad Request | Fix what you sent |
| `401` | Unauthorized | Need to log in / provide a key |
| `403` | Forbidden | Logged in but not allowed |
| `404` | Not Found | Wrong URL or resource doesn't exist |
| `429` | Too Many Requests | Slow down — you're being rate-limited |
| `500` | Internal Server Error | Server crashed, not your fault |

---

## Reading the Browser Network Tab

The Network tab in Chrome DevTools lets you see every HTTP request a page makes — the same requests your Python script will make.

1. Open any website (e.g. a weather site or Perplexity)
2. Open DevTools: `Cmd+Option+I` (Mac) · `F12` or `Ctrl+Shift+I` (Windows)
3. Click the **Network** tab
4. Filter by **Fetch/XHR** — these are the API calls (not images/fonts)
5. Reload the page or trigger an action

Each row is one HTTP request. Click a row to see:
- **Headers** tab: the URL, method, and status code
- **Payload** tab: what was sent (for POST requests)
- **Response** tab: the raw data the server returned — this is what your Python code receives

This is how you reverse-engineer any API: find a site that does what you want, open the Network tab, and read the request it makes.

---

## Walking Through `weather.py`

The final script in `weather.py` is built up in three steps (all shown as commented stages in the file). Here's what each key pattern does:

### `requests.get()` with parameters

```python
response = requests.get(
    f"https://wttr.in/{city}",
    params={"format": "3"},   # becomes ?format=3 in the URL
    timeout=10,               # raises Timeout if server takes > 10s
)
```

`params=` builds the query string automatically. Always set `timeout` — without it, your script can hang forever on a slow network.

### `raise_for_status()` — never skip this

```python
response.raise_for_status()
```

Without this line, a `404` or `500` looks identical to a `200` — the response object exists, `.text` has content, and your code keeps running with garbage data. `raise_for_status()` converts any 4xx/5xx into an exception you can catch.

### `try/except` — specific exceptions, specific messages

```python
try:
    weather_result = get_weather(city)
except requests.HTTPError as e:
    print(f"API error: {e}")          # server returned 4xx or 5xx
except requests.ConnectionError:
    print("Could not connect.")       # no internet, DNS failed
except requests.Timeout:
    print("Request timed out.")       # server too slow
```

List specific exceptions from most-specific to least-specific. A bare `except Exception` hides bugs — avoid it.

### `if __name__ == "__main__"` guard

```python
if __name__ == "__main__":
    main()
```

`__name__` equals `"__main__"` only when Python runs the file directly. When another module imports this file, `__name__` is the module name instead, so `main()` does not auto-run. This is the standard pattern for every runnable Python script.

---

## Break Things Intentionally

Understanding failure modes is as important as making things work.

### 1. Deactivate the virtual environment

```bash
# macOS / Linux
deactivate
python3 weather.py

# Windows
deactivate
python weather.py
```

You'll see:
```
ModuleNotFoundError: No module named 'requests'
```

`requests` is installed inside `.venv` — without activating it, Python can't find the library. Fix: `source .venv/bin/activate`.

### 2. Silence errors by removing `raise_for_status()`

In `weather.py`, comment out the `raise_for_status()` line in `get_weather`, then run:

```bash
python3 weather.py
# Enter: ThisCityDefinitelyDoesNotExist12345
```

The script will print something instead of erroring — wttr.in returns a `200` with fallback content even for bad city names, but other APIs return `404`. Without `raise_for_status()`, your code silently processes bad data. Always leave it in.

---

## Extension Challenges

### 1. Accept city from the command line (`sys.argv`)

Instead of `input()`, read the city from the command line:

```python
import sys

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 weather.py <city>")
        return
    city = sys.argv[1]
    # ... rest of main
```

Run: `python3 weather.py London`

### 2. Loop through multiple cities

```python
cities = ["London", "Tokyo", "Nairobi", "São Paulo"]

for city in cities:
    try:
        print(get_weather(city))
    except Exception as e:
        print(f"{city}: error — {e}")
```

### 3. Interactive loop until the user quits

```python
def main() -> None:
    while True:
        city = input("Enter a city (or 'quit' to exit): ").strip()
        if city.lower() == "quit":
            break
        if not city:
            continue
        try:
            print(get_weather(city))
        except Exception as e:
            print(f"Error: {e}")
```

### 4. Switch to the GitHub API (JSON responses)

The GitHub API is free, requires no key for basic use, and returns JSON:

```python
import requests

def get_user(username: str) -> dict:
    response = requests.get(
        f"https://api.github.com/users/{username}",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()   # `.json()` parses the response body as a dict

user = get_user("torvalds")
print(user["name"])          # Linus Torvalds
print(user["public_repos"]) # number of public repos
print(user["followers"])     # follower count
```

The key difference: `.text` gives you raw text (what wttr.in returns), `.json()` parses JSON into a Python `dict` or `list`.

---

## What's Next

Session 2 introduces **async HTTP** — making multiple API requests at the same time instead of one after another.

```python
# Sync (Session 1): requests one at a time
for city in cities:
    weather = get_weather(city)   # waits for each before starting next

# Async (Session 2): all requests in flight simultaneously
async with httpx.AsyncClient() as client:
    results = await asyncio.gather(*[fetch(client, city) for city in cities])
```

Libraries: `httpx` (async-capable replacement for `requests`) and `asyncio` (Python's built-in async runtime).
