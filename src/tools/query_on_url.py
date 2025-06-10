import time
import requests
from typing import Any, Optional
from gradio_client import Client
from llama_index.core.tools import FunctionTool


client = Client("Agents-MCP-Hackathon/MCP_Server_Web2JSON")


def query_url_tool(url: str) -> str:
    """
    Queries a URL and returns the content as a markdown string.

    Args:
        url (str): The URL to query.

    Returns:
        str: The content of the URL in markdown format.
    """
    # Sleep for 3 seconds to avoid overwhelming the server
    time.sleep(3)
    try:
        result = client.predict(
            content="url",
            is_url=True,
            schema_name="Product",
            api_name="/predict"
        )
        return result

    except requests.exceptions.Timeout:
        return "The request timed out. Please try again later or check the URL."
    except requests.exceptions.RequestException as e:
        return f"Error fetching the webpage: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


Get_info_from_url_tool = FunctionTool.from_defaults(
    name="Get_info_from_url",
    fn=query_url_tool,
    description="Given a product's URL, it returns a JSON object that contains all the important attributes about a product."
)
