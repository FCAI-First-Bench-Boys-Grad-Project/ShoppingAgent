import re
import time
import requests
import markdownify
from typing import Any, Optional
from llama_index.core.tools import FunctionTool
from bs4 import BeautifulSoup
from bs4 import Comment

def visit_webpage(url: str) -> str:
    """
    Visits a webpage at the given url and reads its content as a markdown string.

    Args:
        url (str): The url of the webpage to visit.

    Returns:
        str: The webpage content converted to markdown.
    """
    try:

        # Sleep for 3 seconds to avoid overwhevlming the server
        time.sleep(3)

        # Send a GET request to the URL with a 20-second timeout
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.6",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": "\"Not(A:Brand\";v=\"99\", \"Brave\";v=\"133\", \"Chromium\";v=\"133\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
            
        # Make the HTTP GET request with a timeout.
        response = requests.get(url, headers=headers, timeout=20)
        # response = requests.get(url, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for tag in soup(["script", "style"]):
            tag.decompose()
        
        # Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        
        text = soup.get_text(separator=" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', text)

        # Convert the HTML content to Markdown
        # markdown_content = markdownify.markdownify(soup.text).strip()

        # Remove multiple line breaks
        # markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

        # Truncate to reasonable size
        # max_length = 10000
        # if len(markdown_content) > max_length:
        #     markdown_content = markdown_content[:max_length] + \
        #         "... (content truncated)"

        return clean_text[:10]

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

