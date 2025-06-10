import time
from typing import Any, Optional
from llama_index.core.tools import FunctionTool
from llama_index.tools.duckduckgo import DuckDuckGoSearchToolSpec

def duck_search_tool(query: str) -> str:
    """
    search for a specific query on internet.
    Args:
        query (str): The query to search with.

    Returns:
        str: the result of searching.
    """
    # Sleep for 3 seconds to avoid overwhelming the server
    time.sleep(3)

    tool_spec = DuckDuckGoSearchToolSpec()
    result = tool_spec.duckduckgo_full_search(query)

    return result


search_tool = FunctionTool.from_defaults(
    name="duckduckgo_full_search",
    fn=duck_search_tool,
    description="Make a query to DuckDuckGo search to receive a full search results."
)
