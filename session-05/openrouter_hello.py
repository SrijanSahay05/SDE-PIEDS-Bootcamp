import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
MODEL = "google/gemma-4-31b-it"

async def main():
    client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )

    completion = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assitant. Be brief."},
            {"role": "user", "content": "What is FastApi ?"},
        ],
        max_tokens=256,
    )

    answer = completion.choices[0].message.content
    print(f"Model:   {completion.model}")
    print(f"Answer: {answer}")
    print(f"Tokens used — prompt: {completion.usage.prompt_tokens}, "
          f"completion: {completion.usage.completion_tokens}")


if __name__ == "__main__":
    asyncio.run(main())