# Session 01 — HTTP Requests and API Integration
# Covers: HTTP methods, requests library, GET requests, query params, error handling, user input
# API used: https://wttr.in  (free, no key required)

import requests

# =============================================================================
# HOW HTTP WORKS
# =============================================================================
#
# Every web interaction follows this pattern:
#
#   Client (your script)  →  HTTP Request  →  Server (wttr.in)
#   Client (your script)  ←  HTTP Response ←  Server (wttr.in)
#
# HTTP METHODS — the "verb" that tells the server what you want to do:
#
#   GET     — read/fetch data          (what we use: fetch weather)
#   POST    — send new data to create  (submit a form, send a message)
#   PUT     — replace a resource       (update a full profile)
#   PATCH   — partially update         (change just your email)
#   DELETE  — remove a resource        (delete an account)
#
# STATUS CODES — the server's response to your request:
#
#   200  OK                    — success
#   400  Bad Request           — you sent something wrong
#   401  Unauthorized          — need to log in
#   403  Forbidden             — logged in but not allowed
#   404  Not Found             — URL doesn't exist
#   429  Too Many Requests     — you're being rate-limited
#   500  Internal Server Error — server crashed
#
# We saw all of this live by opening the browser Network tab on Perplexity:
#   Chrome → DevTools (Cmd+Option+I) → Network tab → filter by Fetch/XHR
#   Each row is one HTTP request. Click it to see headers + response body.
#
# =============================================================================


# --- Step 1: Bare GET request ---
# `requests.get(url)` sends an HTTP GET and returns a Response object.
# `raise_for_status()` raises an exception for 4xx/5xx responses.
# Without it, a 404 looks like success — your code keeps running with garbage data.

# response = requests.get("https://wttr.in/PIEDS", timeout=10)
# response.raise_for_status()
# print(response.status_code)   # 200 means success
# print(response.text)          # full weather report (large ASCII art)


# --- Step 2: Wrapping the call in a function ---
# Extract the API call into a reusable function.
# `params=` builds the query string: {"format": "3"} → ?format=3
# `timeout=10` prevents the program from hanging on slow networks.
# Always set a timeout on network calls — never leave it open-ended.

# def get_weather(city: str) -> str:
#     response = requests.get(
#         f"https://wttr.in/{city}",
#         params={"format": "3"},   # "3" = compact one-liner: city + temp + condition
#         timeout=10,
#     )
#     response.raise_for_status()
#     return response.text.strip()   # strip trailing newline the API adds


# --- Step 3: Adding user input and error handling ---
# `input().strip()` reads a line from the user and removes surrounding whitespace.
# `try/except` catches network or HTTP errors without crashing the program.
# Multiple `except` clauses let you give specific messages for different failures.

# def get_weather(city: str) -> str:
#     response = requests.get(
#         f"https://wttr.in/{city}",
#         params={"format": "3"},
#         timeout=10,
#     )
#     response.raise_for_status()
#     return response.text.strip()

# def main() -> None:
#     city = input("Enter a city: ").strip()
#     if not city:           # empty string is falsy in Python
#         print("No city entered.")
#         return
#
#     try:
#         weather_result = get_weather(city)
#         print(f"Result: {weather_result}")
#     except requests.HTTPError as e:
#         print(f"API error: {e}")
#     except requests.ConnectionError:
#         print("Could not connect. Check your internet connection.")
#     except requests.Timeout:
#         print("Request timed out. The server took too long.")

# if __name__ == "__main__":
#     main()


# --- Final version: complete, runnable program ---
# Requires an internet connection.

def get_weather(city: str) -> str:
    """Fetch a one-line weather summary for the given city from wttr.in."""
    response = requests.get(
        f"https://wttr.in/{city}",
        params={"format": "3"},   # compact format: "City: +25°C ⛅ Partly cloudy"
        timeout=10,
    )
    response.raise_for_status()        # raise HTTPError on 4xx/5xx — never swallow errors
    return response.text.strip()       # strip trailing newline the API always appends


def main() -> None:
    city = input("Enter a city: ").strip()   # strip removes accidental leading/trailing spaces
    if not city:
        print("No city entered.")
        return

    try:
        weather_result = get_weather(city)
        print(f"Result: {weather_result}")
    except requests.HTTPError as e:
        print(f"API error: {e}")             # e.g. 404 if wttr.in can't find the city
    except requests.ConnectionError:
        print("Could not connect. Check your internet connection.")
    except requests.Timeout:
        print("Request timed out. The server took too long.")


# `if __name__ == "__main__"` ensures main() only runs when this file is
# executed directly — not when it is imported by another module.
if __name__ == "__main__":
    main()
