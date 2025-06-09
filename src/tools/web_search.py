from typing import Any, Optional
from llama_index.core.tools import FunctionTool
from llama_index.tools.duckduckgo import DuckDuckGoSearchToolSpec

# Direct usage of DuckDuckGoSearchToolSpec
search_tool = DuckDuckGoSearchToolSpec().to_tool_list()