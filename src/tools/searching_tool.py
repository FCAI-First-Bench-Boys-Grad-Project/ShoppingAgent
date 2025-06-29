from langchain_core.tools import tool
from typing import List, Optional
from tavily import TavilyClient
import os
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


@tool
def search_tool(query: str, max_results: int = 5) -> List[str]:
    """searches the web for the given query and returns a list of URLs"""
    response = tavily_client.search(
        query=query, max_results=max_results)
    results = []
    for i in range(len(response['results'])):
        results.append(response['results'][i].get('url', 'No URL found'))
    return results
