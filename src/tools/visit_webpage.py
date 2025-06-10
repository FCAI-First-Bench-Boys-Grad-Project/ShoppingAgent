import re
import time
import requests
import markdownify
from typing import Any, Optional
from llama_index.core.tools import FunctionTool


def visit_webpage(url: str) -> str:
    """
    Visits a webpage at the given url and reads its content as a markdown string.

    Args:
        url (str): The url of the webpage to visit.

    Returns:
        str: The webpage content converted to markdown.
    """
    try:

        # Sleep for 3 seconds to avoid overwhelming the server
        time.sleep(3)

        # Send a GET request to the URL with a 20-second timeout
        response = requests.get(url, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Convert the HTML content to Markdown
        markdown_content = markdownify.markdownify(response.text).strip()

        # Remove multiple line breaks
        markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

        # Truncate to reasonable size
        max_length = 10000
        if len(markdown_content) > max_length:
            markdown_content = markdown_content[:max_length] + \
                "... (content truncated)"

        return markdown_content

    except requests.exceptions.Timeout:
        return "The request timed out. Please try again later or check the URL."
    except requests.exceptions.RequestException as e:
        return f"Error fetching the webpage: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# Create a LlamaIndex tool
visit_webpage_tool = FunctionTool.from_defaults(
    name="visit_webpage",
    fn=visit_webpage,
    description="Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages."
)
