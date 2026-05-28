# Session 01 — Functions, Type Hints, and String Methods
# Covers: defining functions, return types, default parameters, string built-ins
# These are the Python building blocks used directly in weather.py


# --- Step 1: Basic function with a return value ---
# `name: str` is a type hint — it documents expected input type.
# `-> str` documents what the function returns.
# Type hints are NOT enforced at runtime; they help editors and readers.

# def greet(name: str) -> str:
#     return f"Hello, {name}"

# res = greet("rahul")
# print(res)   # Hello, rahul


# --- Step 2: Passing the wrong type (type hints are advisory, not enforced) ---
# Python won't raise an error here, but tools like mypy will flag it.

# res = greet(10)   # passes an int — no crash, but bad practice
# print(res)        # Hello, 10


# --- Step 3: `-> None` return type + default parameter ---
# When a function only prints (side effect, no return value), use `-> None`.
# Default parameters let callers omit that argument.

# def greet(name: str, greetings: str = "Hello") -> None:
#     print(f"{greetings}, {name}")

# greet(name="Srijan", greetings="Hi")   # Hi, Srijan
# greet(name="Rahul")                    # Hello, Rahul  (uses default)


# --- Step 4: Multiple parameters + f-string formatting ---
# Functions can take as many typed parameters as needed.
# Keyword arguments make call sites self-documenting.

# def describe_weather(city: str, temp: int, condition: str) -> str:
#     return f"{city}: {temp}C, {condition}"

# print(describe_weather("Pilani", 40, "Partly cloudy"))
# Output: Pilani: 40C, Partly cloudy


# --- Step 5: String methods ---
# Strings in Python have built-in methods.
# Methods can be chained — each call returns a new string.

city = "   Mumbai   "
print(city)              # '   Mumbai   '  — raw value with spaces
print(city.strip())      # 'Mumbai'        — removes leading/trailing whitespace
print(city.lower())      # '   mumbai   '  — lowercase (spaces preserved)
print(city.strip().upper())  # 'MUMBAI'   — chain: strip first, then uppercase
