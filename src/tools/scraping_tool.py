from gradio_client import Client
import time
import requests
from langchain_core.tools import tool


client = Client("garage-lab/MCP_STRUCTRA")


@tool
def query_url_tool(data_schema: str, url: str) -> str:
    """
    Extracts structured data from a webpage using a custom schema definition.

    Use this tool to parse and extract specific information from web pages in a 
    structured format. Perfect for:
    - Product information (prices, descriptions, availability)
    - Article metadata (title, author, publish date, summary)
    - Contact information (addresses, phone numbers, emails)
    - Event details (dates, locations, ticket prices)
    - Technical documentation (API endpoints, parameters)
    - News articles (headlines, content, sources)

    Args:
        data_schema (str): Schema defining what data to extract and in what format.
                          Supports multiple formats (see examples below).
        url (str): The target webpage URL to extract data from.

    Returns:
        str: Extracted data formatted according to your schema. Returns error 
             message if URL is inaccessible or extraction fails.

    **Schema Format Examples:**
    JSON Schema:
    ```json
    {
      "properties": {
        "product_name": {"type": "string", "description": "Product title"},
        "price": {"type": "number", "description": "Current price in USD"},
        "rating": {"type": "number", "description": "Average rating (1-5)"},
        "in_stock": {"type": "boolean", "description": "Availability status"},
        "reviews": {"type": "array", "description": "Recent customer reviews"}
      },
      "required": ["product_name", "price"]
    }
    ```
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
