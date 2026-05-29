import time
import requests

cities = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
          "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat"]

def sync_get_weather(city: str) -> str:
    """Fetch a one-line weather summary for the given city from wttr.in."""
    response = requests.get(
        f"https://wttr.in/{city}",
        params={"format": "3"},   # compact format: "City: +25°C ⛅ Partly cloudy"
        timeout=10,
    )
    response.raise_for_status()        # raise HTTPError on 4xx/5xx — never swallow errors
    return response.text.strip()       # strip trailing newline the API always appends

start = time.perf_counter()
print("Synchronous Calls: ")
for city in cities:
    if not city:
        print("No city entered.")
        continue
    try:
        weather_result = sync_get_weather(city)
        print(f"Result: {weather_result}")
    except requests.HTTPError as e:
        print(f"API error: {e}")             # e.g. 404 if wttr.in can't find the city
    except requests.ConnectionError:
        print("Could not connect. Check your internet connection.")
    except requests.Timeout:
        print("Request timed out. The server took too long.")
print(f"\n{time.perf_counter() - start:.2f}s")

print("----------------")
