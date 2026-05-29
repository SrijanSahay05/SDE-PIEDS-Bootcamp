import asyncio
import httpx
import time

CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat",
]

async def get_weather(client: httpx.AsyncClient, city: str, sem) -> str:
    async with sem:
        response = await client.get(
            f"https://wttr.in/{city}",
            params={"format": "3"}, 
            timeout=10
        )
        response.raise_for_status()        
        return response.text.strip() 


async def main() -> None:
    sem = asyncio.Semaphore(5)
    start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[get_weather(client, city, sem) for city in CITIES],
            return_exceptions=True,
        )
    
    elapsed_time = time.perf_counter() - start

    for city, result in zip(CITIES, results):
        if isinstance(result, Exception):
            print(f"{city}: Error - {result}")
        else:
            print(result)

    print(f"\nFetched {len(CITIES)} cities in {elapsed_time:.2f}s")

asyncio.run(main())