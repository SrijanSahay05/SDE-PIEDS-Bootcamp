from tavily import TavilyClient
import os 
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
response = tavily_client.search("Who is Leo Messi?")

print(response)


