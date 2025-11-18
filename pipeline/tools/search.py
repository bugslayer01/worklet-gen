from dotenv import load_dotenv
from tavily import TavilyClient
import os
import asyncio
import time

load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")

# Initialize Tavily client
client = TavilyClient(api_key=tavily_api_key)


async def search_tavily(query: str, max_results: int = 4, depth: str = "advanced", include_answer: bool = True, include_favicon: bool = True):
    """
    Perform an asynchronous web search using Tavily API with retry logic.

    Args:
        query (str): The search query string.
        max_results (int): Maximum number of results to return (default=5).
        depth (str): Search depth, "basic" or "advanced" (default="advanced").
        answer_off (bool): Whether to include answer snippets (default=False).
        exclude_favicon (bool): Whether to exclude favicon images from results (default=False).

    Returns:
        dict: Tavily API response containing search results, or empty dict on failure.
    """
    attempts = 0
    while attempts < 5:
        try:
            return await asyncio.to_thread(
                client.search,
                query=query,
                include_answer="advanced" if include_answer else None,
                search_depth=depth,
                max_results=max_results,
                include_favicon=True if include_favicon else False,
            )
        except Exception as e:
            attempts += 1
            print(f"Tavily search attempt {attempts} failed: {e}")
            if attempts >= 5:
                return {}
            await asyncio.sleep(1)
