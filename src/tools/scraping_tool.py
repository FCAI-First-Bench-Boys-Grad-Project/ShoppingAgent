from gradio_client import Client
import time
import requests
from langchain_core.tools import tool


client = Client("garage-lab/MCP_WEB2JSON")

#TODO: give power to the agent to choose the schema to use
@tool
def query_url_tool(data_schema: str, url: str) -> str:
    """
    Queries a URL and returns the content as a markdown string.

    Args:
        url (str): The URL to query.

    Returns:
        str: The content of the URL in markdown format.
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
