from langchain_core.tools import tool
from typing import List
from tavily import TavilyClient
import os
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


@tool
def search_tool(query: str, max_results: int = 3) -> List[str]:
    """
    Performs a web search and returns relevant URLs.

    Use this tool when you need to find current information, recent news, 
    or web resources that are not in your training data. Best for:
    - Current events or breaking news
    - Recent product releases or updates  
    - Live data (stock prices, weather, sports scores)
    - Specific websites or resources to reference
    - Fact-checking recent claims or statements

    Args:
        query (str): Search terms - keep concise and specific for best results
        max_results (int): Number of URLs to return (default: 3, recommended: 3-10)

    Returns:
        List[str]: List of URLs from search results. Use these URLs with other 
                   tools to fetch and analyze the actual content.

    Example usage:
        - search_tool("nvidia stock price today")  # Current financial data
        - search_tool("ukraine war latest news january 2025")  # Recent events
        - search_tool("best practices microservices architecture", max_results=5)  # Technical guides
        - search_tool("taylor swift eras tour 2025 dates")  # Event information
        - search_tool("openai gpt-5 announcement")  # Product releases
        - search_tool("python 3.13 new features documentation")  # Technical docs
        - search_tool("site:github.com tensorflow tutorials")  # Search specific website
        - search_tool("react hooks site:reactjs.org")  # Official documentation from specific site
    """
    response = tavily_client.search(
        query=query, max_results=max_results)
    results = []
    for i in range(len(response['results'])):
        results.append(response['results'][i].get('url', 'No URL found'))
    return results
