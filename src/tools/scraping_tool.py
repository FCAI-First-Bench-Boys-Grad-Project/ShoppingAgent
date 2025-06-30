from gradio_client import Client
import time
import requests
from langchain_core.tools import tool


client = Client("garage-lab/MCP_WEB2JSON")


@tool
def query_url_tool(data_schema: str, url: str) -> str:
    """
    Queries a URL and returns its content as a markdown string.

    Args:
        url (str): The URL to query.
        data_schema (str): The schema to use for the data extraction.
        for example:
        title: str = Page title
        price: float = Product price
        description: str = Product description
        available: bool = Is available

    Returns:
        str: The content of the URL in the format of whatever schema you give it.
    """
    # Sleep for 2 seconds to avoid overwhelming the server
    time.sleep(2)
    try:
        result = client.predict(
            content=url,
            is_url=True,
            schema_input=data_schema,
            api_name="/predict"
        )
        return str(result)

    except requests.exceptions.Timeout:
        return "The request timed out. Please try again later or check the URL."
    except requests.exceptions.RequestException as e:
        return f"Error fetching the webpage: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# print(query_url_tool(
#     "https://www.amazon.com/Google-Pixel-Gemini-Smartphone-Incredible/dp/B0DVHV7N4X?th=1")
# )
