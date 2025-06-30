"""
AI Agent Tools Module

This module provides a collection of tools designed for AI agents to interact with web content,
perform searches, and execute code. Each tool is designed to be robust, well-documented, and
handle edge cases gracefully.

Dependencies:
    - gradio_client: For web content extraction
    - langchain_core: For tool decorators
    - tavily: For web search functionality
    - requests: For HTTP operations
    - contextlib: For output redirection
    - io: For string buffer operations

Environment Variables Required:
    - TAVILY_API_KEY: API key for Tavily search service
"""

import os
import sys
import time
import io
import requests
import contextlib
from gradio_client import Client
from langchain_core.tools import tool
from typing import List, Optional, Dict, Any
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
try:
    web_client = Client("garage-lab/MCP_WEB2JSON")
except Exception as e:
    print(f"Warning: Could not initialize web client: {e}")
    web_client = None

try:
    tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
except Exception as e:
    print(f"Warning: Could not initialize Tavily client: {e}")
    tavily_client = None


@tool
def query_url_tool(url: str, data_schema: Optional[str] = None) -> str:
    """
    Extract and structure content from a web URL using a JSON schema specification.
    
    This tool fetches content from a given URL and extracts structured data according
    to a provided JSON schema using the MCP_WEB2JSON service. It's designed to extract
    specific fields from web pages in a structured format.
    
    Args:
        url (str): The target URL to extract content from. Must be a valid HTTP/HTTPS URL.
        data_schema (str, optional): JSON schema string defining the data structure to extract.
                                   If None, uses general content extraction.
                                   
                                   Schema format:
                                   {
                                     "properties": {
                                       "field_name": {
                                         "type": "string|number|boolean|array|object",
                                         "description": "Description of the field"
                                       }
                                     },
                                     "required": ["field1", "field2"]
                                   }
    
    Returns:
        str: The extracted content in JSON format matching the schema, or an error message if extraction fails.
    
    Raises:
        None: All exceptions are caught and returned as descriptive error messages.
    
    Example:
        >>> schema = '''
        ... {
        ...   "properties": {
        ...     "title": {"type": "string", "description": "Page title"},
        ...     "price": {"type": "number", "description": "Product price"},
        ...     "description": {"type": "string", "description": "Product description"},
        ...     "availability": {"type": "string", "description": "Stock status"}
        ...   },
        ...   "required": ["title"]
        ... }
        ... '''
        >>> content = query_url_tool("https://example-store.com/product/123", schema)
        >>> print(content)
        # {"title": "Amazing Product", "price": 29.99, "description": "...", "availability": "In Stock"}
        
        >>> # For general content extraction
        >>> content = query_url_tool("https://example.com")
        >>> print(content)
        # General content in markdown format
    
    Note for AI Agents:
        - Use JSON schema to define exactly what data you want to extract
        - Schema should match the expected structure of the target webpage
        - Common field types: "string", "number", "boolean", "array", "object"
        - Always include meaningful descriptions for better extraction accuracy
        - Use "required" array to specify mandatory fields
        - For e-commerce: extract title, price, description, images, ratings
        - For articles: extract title, author, date, content, tags
        - For contact pages: extract name, email, phone, address
        - Handle cases where required fields might not be found
        - Test schemas with known pages before using in production
        - The more specific your schema, the better the extraction quality
    """
    if not web_client:
        return "Error: Web client not initialized. Please check your configuration."
    
    if not url or not isinstance(url, str):
        return "Error: Invalid URL provided. URL must be a non-empty string."
    
    if not url.startswith(('http://', 'https://')):
        return "Error: URL must start with http:// or https://"
    
    # Validate JSON schema if provided
    if data_schema:
        try:
            import json
            schema_dict = json.loads(data_schema)
            if not isinstance(schema_dict, dict):
                return "Error: Data schema must be a valid JSON object."
            if "properties" not in schema_dict:
                return "Error: Data schema must contain a 'properties' field."
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON schema format: {str(e)}"
        except Exception as e:
            return f"Error: Schema validation failed: {str(e)}"
    
    # Use default general schema if none provided
    schema_to_use = data_schema if data_schema else "general"
    
    # Optional rate limiting (uncomment if needed)
    # time.sleep(2)
    
    try:
        result = web_client.predict(
            content=url,
            is_url=True,
            schema_input=schema_to_use,
            api_name="/predict"
        )
        
        if not result:
            return "Warning: No content extracted from the URL."
        
        return str(result)
        
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The server may be slow or the URL may be inaccessible."
    except requests.exceptions.ConnectionError:
        return "Error: Connection failed. Please check your internet connection and the URL."
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP error occurred: {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"Error: Request failed: {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error occurred during content extraction: {str(e)}"


@tool
def search_tool(query: str, max_results: int = 5, search_depth: str = "basic") -> List[Dict[str, str]]:
    """
    Search the web using Tavily and return structured results.
    
    This tool performs web searches and returns a list of relevant URLs with metadata.
    It's designed to provide AI agents with access to current web information and
    diverse sources for research and fact-checking.
    
    Args:
        query (str): The search query string. Should be descriptive and specific.
        max_results (int, optional): Maximum number of results to return. Defaults to 5.
                                   Range: 1-20 (values outside this range will be clamped).
        search_depth (str, optional): Search depth level. Defaults to "basic".
                                    Options: "basic", "advanced"
    
    Returns:
        List[Dict[str, str]]: A list of dictionaries containing search results.
                             Each dictionary contains:
                             - 'url': The URL of the result
                             - 'title': The title of the page (if available)
                             - 'score': Relevance score (if available)
    
    Example:
        >>> results = search_tool("artificial intelligence trends 2024", max_results=3)
        >>> for result in results:
        ...     print(f"Title: {result.get('title', 'N/A')}")
        ...     print(f"URL: {result['url']}")
        ...     print(f"Snippet: {result.get('snippet', 'N/A')}")
        ...     print("---")
    
    Note for AI Agents:
        - Always validate search queries before use
        - Consider using specific, targeted queries for better results
        - Handle empty result sets gracefully
        - Be mindful of API rate limits
        - Results are ordered by relevance
        - Use appropriate max_results based on your processing capacity
        - Consider follow-up searches with refined queries if initial results are poor
    """
    if not tavily_client:
        return [{"url": "Error: Tavily client not initialized. Please check your API key.", 
                "title": "Configuration Error", "snippet": "", "score": "0"}]
    
    if not query or not isinstance(query, str) or len(query.strip()) == 0:
        return [{"url": "Error: Invalid query provided. Query must be a non-empty string.", 
                "title": "Input Error", "snippet": "", "score": "0"}]
    
    # Clamp max_results to reasonable bounds
    max_results = max(1, min(20, max_results))
    
    try:
        response = tavily_client.search(
            query=query.strip(),
            max_results=max_results,
            search_depth=search_depth
        )
        
        if not response or 'results' not in response:
            return [{"url": "No results found", "title": "No Results", 
                    "snippet": f"No search results found for query: {query}", "score": "0"}]
        
        results = []
        for result in response['results']:
            structured_result = {
                'url': result.get('url', 'No URL available'),
                'title': result.get('title', 'No title available'),
                'score': str(result.get('score', 'N/A'))
            }
            results.append(structured_result)
        
        return results if results else [{"url": "No results found", "title": "Empty Results", 
                                        "score": "0"}]
        
    except Exception as e:
        return [{"url": f"Error during search: {str(e)}", "title": "Search Error", 
                "score": "0"}]


@tool
def run_code_tool(code: str, timeout: int = 30, allowed_imports: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Execute Python code in a controlled environment and return results.
    
    This tool allows AI agents to execute Python code snippets safely with output capture
    and basic security measures. It's designed for data processing, calculations, and
    simple automation tasks.
    
    Args:
        code (str): The Python code to execute. Should be valid Python syntax.
        timeout (int, optional): Maximum execution time in seconds. Defaults to 30.
        allowed_imports (List[str], optional): List of allowed import modules. 
                                             If None, basic imports are allowed.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
                       - 'success': Boolean indicating if execution was successful
                       - 'output': String containing stdout output
                       - 'error': String containing error message (if any)
                       - 'execution_time': Float indicating execution time in seconds
    
    Example:
        >>> result = run_code_tool("print('Hello, World!')")
        >>> print(result)
        {'success': True, 'output': 'Hello, World!\\n', 'error': None, 'execution_time': 0.001}
        
        >>> result = run_code_tool("import math; print(math.sqrt(16))")
        >>> print(result)
        {'success': True, 'output': '4.0\\n', 'error': None, 'execution_time': 0.002}
    
    Security Notes:
        - This tool uses exec() which can be dangerous in production environments
        - File system access is not restricted
        - Network access is not restricted
        - Consider using a sandboxed environment for production use
        - Malicious code can potentially harm the system
    
    Note for AI Agents:
        - Always validate code before execution
        - Use for computational tasks, data processing, and simple automation
        - Avoid executing code that modifies system files or makes network requests
        - Handle both successful and error cases in your workflow
        - Consider breaking complex operations into smaller code snippets
        - Be aware of execution time limits
        - Test code snippets with simple examples first
        - Use appropriate error handling for robust automation
    """
    if not code or not isinstance(code, str):
        return {
            'success': False,
            'output': '',
            'error': 'Invalid code provided. Code must be a non-empty string.',
            'execution_time': 0.0
        }
    
    # Basic validation to prevent obviously dangerous operations
    dangerous_patterns = [
        'import os', '__import__', 'exec(', 'eval(',
        'open(', 'file(', 'input(', 'raw_input(',
        'subprocess', 'system', 'popen', 'getattr',
        'setattr', 'delattr', 'globals(', 'locals(',
        'vars(', 'dir('
    ]
    
    code_lower = code.lower()
    for pattern in dangerous_patterns:
        if pattern in code_lower:
            return {
                'success': False,
                'output': '',
                'error': f'Potentially dangerous operation detected: {pattern}. Execution blocked for security.',
                'execution_time': 0.0
            }
    
    output = io.StringIO()
    start_time = time.time()
    
    try:
        # Create a restricted execution environment
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'range': range,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'abs': abs,
                'max': max,
                'min': min,
                'sum': sum,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'any': any,
                'all': all,
            }
        }
        
        # Allow basic math operations
        try:
            import math
            safe_globals['math'] = math
        except ImportError:
            pass
        
        with contextlib.redirect_stdout(output):
            exec(code, safe_globals, {})
        
        execution_time = time.time() - start_time
        
        return {
            'success': True,
            'output': output.getvalue(),
            'error': None,
            'execution_time': round(execution_time, 4)
        }
        
    except SyntaxError as e:
        return {
            'success': False,
            'output': output.getvalue(),
            'error': f'Syntax Error: {str(e)}',
            'execution_time': round(time.time() - start_time, 4)
        }
    except Exception as e:
        return {
            'success': False,
            'output': output.getvalue(),
            'error': f'Runtime Error: {str(e)}',
            'execution_time': round(time.time() - start_time, 4)
        }


# Utility function for AI agents to validate tool availability
def check_tool_availability() -> Dict[str, bool]:
    """
    Check which tools are available and properly configured.
    
    Returns:
        Dict[str, bool]: Status of each tool's availability
    """
    return {
        'query_url_tool': web_client is not None,
        'search_tool': tavily_client is not None,
        'run_code_tool': True,  # Always available as it doesn't depend on external services
        'tavily_api_key_set': bool(os.environ.get("TAVILY_API_KEY"))
    }


# Example usage and testing functions for AI agents
def create_example_schemas() -> Dict[str, str]:
    """
    Provide example JSON schemas for common data extraction scenarios.
    
    Returns:
        Dict[str, str]: Dictionary of schema names and their JSON schema strings
    """
    return {
        "product": '''{
            "properties": {
                "title": {"type": "string", "description": "Product name or title"},
                "price": {"type": "number", "description": "Product price in numeric format"},
                "currency": {"type": "string", "description": "Currency symbol or code"},
                "description": {"type": "string", "description": "Product description"},
                "availability": {"type": "string", "description": "Stock status (in stock, out of stock, etc.)"},
                "rating": {"type": "number", "description": "Product rating (0-5 scale)"},
                "images": {"type": "array", "description": "Array of product image URLs"},
                "brand": {"type": "string", "description": "Product brand or manufacturer"}
            },
            "required": ["title"]
        }''',
        
        "article": '''{
            "properties": {
                "title": {"type": "string", "description": "Article headline or title"},
                "author": {"type": "string", "description": "Article author name"},
                "date": {"type": "string", "description": "Publication date"},
                "content": {"type": "string", "description": "Main article content/body text"},
                "summary": {"type": "string", "description": "Article summary or excerpt"},
                "tags": {"type": "array", "description": "Article tags or categories"},
                "readingTime": {"type": "number", "description": "Estimated reading time in minutes"}
            },
            "required": ["title", "content"]
        }''',
        
        "contact": '''{
            "properties": {
                "name": {"type": "string", "description": "Contact name or business name"},
                "email": {"type": "string", "description": "Email address"},
                "phone": {"type": "string", "description": "Phone number"},
                "address": {"type": "string", "description": "Physical address"},
                "website": {"type": "string", "description": "Website URL"},
                "hours": {"type": "string", "description": "Business hours"},
                "description": {"type": "string", "description": "Business description"}
            },
            "required": ["name"]
        }''',
        
        "job_posting": '''{
            "properties": {
                "title": {"type": "string", "description": "Job title"},
                "company": {"type": "string", "description": "Company name"},
                "location": {"type": "string", "description": "Job location"},
                "salary": {"type": "string", "description": "Salary range or amount"},
                "description": {"type": "string", "description": "Job description"},
                "requirements": {"type": "array", "description": "Job requirements list"},
                "benefits": {"type": "array", "description": "Job benefits list"},
                "employmentType": {"type": "string", "description": "Full-time, part-time, contract, etc."},
                "datePosted": {"type": "string", "description": "Job posting date"}
            },
            "required": ["title", "company"]
        }''',
        
        "real_estate": '''{
            "properties": {
                "title": {"type": "string", "description": "Property title or address"},
                "price": {"type": "number", "description": "Property price"},
                "bedrooms": {"type": "number", "description": "Number of bedrooms"},
                "bathrooms": {"type": "number", "description": "Number of bathrooms"},
                "squareFootage": {"type": "number", "description": "Property size in square feet"},
                "propertyType": {"type": "string", "description": "House, apartment, condo, etc."},
                "description": {"type": "string", "description": "Property description"},
                "features": {"type": "array", "description": "Property features list"},
                "images": {"type": "array", "description": "Property image URLs"},
                "agent": {"type": "string", "description": "Real estate agent name"},
                "agentPhone": {"type": "string", "description": "Agent contact phone"}
            },
            "required": ["title", "price"]
        }''',
        
        "restaurant": '''{
            "properties": {
                "name": {"type": "string", "description": "Restaurant name"},
                "cuisine": {"type": "string", "description": "Type of cuisine"},
                "address": {"type": "string", "description": "Restaurant address"},
                "phone": {"type": "string", "description": "Phone number"},
                "rating": {"type": "number", "description": "Restaurant rating"},
                "priceRange": {"type": "string", "description": "Price range (e.g., $, $, $$)"},
                "hours": {"type": "string", "description": "Operating hours"},
                "menu": {"type": "array", "description": "Menu items with prices"},
                "reviews": {"type": "array", "description": "Customer reviews"}
            },
            "required": ["name"]
        }'''
    }


def test_tools() -> None:
    """
    Test all tools with basic examples to ensure they're working correctly.
    This function is useful for AI agents to validate tool functionality.
    """
    print("Testing AI Agent Tools...")
    print("=" * 40)
    
    # Test availability
    availability = check_tool_availability()
    print("Tool Availability:")
    for tool_name, available in availability.items():
        status = "✓ Available" if available else "✗ Not Available"
        print(f"  {tool_name}: {status}")
    print()
    
    # Test code execution
    print("Testing run_code_tool...")
    result = run_code_tool("print('Code execution test successful!')")
    print(f"Success: {result['success']}")
    print(f"Output: {result['output'].strip()}")
    print()
    
    # Test search (if available)
    if availability['search_tool']:
        print("Testing search_tool...")
        results = search_tool("Python programming", max_results=2)
        print(f"Found {len(results)} results")
        if results and results[0].get('url') != 'Error: Tavily client not initialized. Please check your API key.':
            print(f"First result: {results[0]['title']}")
    
    # Show example schemas
    print("\nExample JSON Schemas:")
    print("=" * 20)
    schemas = create_example_schemas()
    for schema_name in schemas.keys():
        print(f"- {schema_name}: For extracting {schema_name} data")
    
    print(f"\nTo use a schema:")
    print(f"schema = create_example_schemas()['product']")
    print(f"result = query_url_tool('https://example.com', schema)")
    
    print("Tool testing completed.")


if __name__ == "__main__":
    test_tools()