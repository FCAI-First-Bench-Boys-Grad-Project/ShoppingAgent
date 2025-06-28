from src.llm_client import *
from src.google_search import *
import os
import dotenv
import sys
import time
import threading
import yaml # <-- IMPORT YAML
from gradio_client import Client
import json_repair


dotenv.load_dotenv()


async def search_urls(query: str, max_results: int = 10) -> List[str]:
    """Simple function to get URLs from Google search"""
    async with GoogleURLScraper(headless=True) as scraper:
        urls = await scraper.get_search_urls(query, max_results)
        return urls

def search(query: str, max_results: int = 10) -> List[str]:
    """Synchronous wrapper for search_urls"""
    return asyncio.run(search_urls(query, max_results))


def extract_info_from_url(url: str, json_schema: dict) -> dict:
    """Extracts information from a given URL using a JSON schema."""
    json_schema = json_repair.repair_json(str(json_schema))  # Ensure the JSON schema is valid

    client = Client("garage-lab/MCP_WEB2JSON")
    result = client.predict(
            content=url,
            is_url=True,
            schema_input=json_schema,
            api_name="/predict"
    )
    return result


def load_prompts(file_path: str = "prompts.yaml") -> dict:
    """Loads system prompts from a YAML file."""
    try:
        with open(file_path, 'r') as file:
            prompts = yaml.safe_load(file)
            return prompts
    except FileNotFoundError:
        print(f"Error: Prompt file not found at '{file_path}'.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None

search_tool = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the web and return relevant URLs for a given query",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query - use specific keywords, phrases, and context from the user's question"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of URLs to return (default: 10). Adjust based on how thorough your research needs to be.",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
    }
}

extract_info_tool = {
    "type": "function",
    "function": {
        "name": "extract_info_from_url",
        "description": "Extract structured information from any webpage using a custom JSON schema. Perfect for QA tasks, fact-checking, and gathering specific details. all attributes should be one of the following: string, integer, boolean, float.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to extract information from. Must be a valid HTTP/HTTPS URL."
                },
                "json_schema": {
                    "type": "object",
                    "description": "JSON schema defining what information to extract. Must include 'properties' object with field definitions including 'type' and 'description'. Can include 'required' array for mandatory fields.",
                    "properties": {
                        "properties": {
                            "type": "object",
                            "description": "Object defining the fields to extract"
                        },
                        "required": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of required field names"
                        }
                    },
                    "required": ["properties"]
                }
            },
            "required": ["url", "json_schema"]
        }
    }
}

tools = [search_tool,extract_info_tool]
llm_client = NVIClient(tools_func=[search,extract_info_from_url],tools_info=tools, api_key=os.environ["NVIDIA_API_KEY"])

all_prompts = load_prompts("src/prompts/sys.yaml")  # Load prompts from YAML file
memory = {
    "general": [],
    "query_clarifier": [{'role': 'system', 'content': all_prompts['query_clarifier']['prompt']}],
    "product_researcher": [{'role': 'system', 'content': all_prompts['product_researcher']['prompt']}],
}



def chat():
    """
    Starts a simple, continuous command-line chat session with the LLM.
    """

    print("Chat with the AI assistant. Type 'quit' or 'exit' to end the session.")
    print("-" * 30)            
    
    current_memory = memory["query_clarifier"]
    query_clarified = False

    while True:
        try:
            # 1. Get user input
            user_input = input("You: ")

            if user_input.lower() in ["quit", "exit"]:
                print("Assistant: Goodbye!")
                break

            print("Assistant: ...thinking...")
            llm_client.set_memory(current_memory)  # Set the current memory for the LLM client

            

            response,_ = llm_client.generate_complete_response(
                message=user_input,
                reason=False  # Assuming you want reasoning in the response
            )

            print(f"Assistant: {response}")

            criteria = user_input
            if 'proceed' not in response.lower():
                user_input = input("You: ")
                prompt = "Based on the previous response and the current response, summarize what the user wants in built points including the user query.  \n User input: "
                response,_ = llm_client.generate_complete_response(
                    message=prompt + user_input,
                    reason=False  # Assuming you want reasoning in the response
                )
                criteria = response
            print(f"Assistant: Alright I will be using the following criteria: {criteria}")

            # Show a loading animation while searching

            
            create_shopping_list(criteria)  # Call the function to create a shopping list

        except KeyboardInterrupt:
            print("\nAssistant: Goodbye!")
            #saving the memory to a file
            with open("memory.yaml", "w") as file:
                llm_client.save_log(filename="llm_log.txt")  # Save the log to a file
                yaml.dump(memory, file)
            break
    with open("memory.yaml", "w") as file:
        yaml.dump(memory, file)
        llm_client.save_log(filename="llm_log.json")  # Save the log to a file

            
        # except Exception as e:
        #     print(f"An error occurred: {e}")
        #     # Optionally, you might want to break the loop on error
        #     # break

def create_shopping_list(criteria: str) -> List[str]:
    """
    Creates a shopping list based on the provided criteria.
    Should return a list of urls.
    """
    print(f"Creating shopping list based on criteria: {criteria}")
    
    # Okay
    print('\n')
    print('-' * 30)
    print('-' * 30)

    llm_client.set_memory(memory["product_researcher"])  # Set the general memory for the LLM client
    tool_calls = [True]  # Initialize with a non-empty list to enter the loop
    response, tool_calls = llm_client.generate_complete_response(
        message=f"Start searching using this criteria: {criteria}",
        use_tools=True, 
        reason=True)
    print(f"Assistant: {response}")
    terminate = False
    while not terminate:
        response, tool_calls = llm_client.generate_complete_response(
            message=f"""
            PRODUCT SEARCH REFLECTION

            Analyze your product research:
            - How many viable PRODUCTS did you find that match the criteria: {criteria}?
            - What key product details are missing (prices, specs, reviews, availability)?
            - Which product categories or retailers haven't you explored yet?

            DECISION: Do you have enough quality products to make solid recommendations?
            - YES → Stop and provide your product recommendations with comparisons and a ecommerce link for each recommendation
            - NO → Make 1-2 targeted searches on shopping sites, review sites, or manufacturer pages for missing products

            Focus on finding actual purchasable products, not just product information. Stop when you have 3-5 solid options to recommend with actual ecommerce product links.
            YOU ARE ALLOWED TO MAKE ASSUMPTIONS ABOUT THE USER'S NEEDS BASED ON THE CRITERIA PROVIDED.
            BUT YOU NEED TO PROVIDE A REASONING FOR YOUR ASSUMPTIONS AND WHY YOU CHOSE THE PRODUCTS YOU DID.
            IF YOU ALREADY HAVE LINKS TO PRODUCTS THEN BASE ALL YOUR OUTPUTS USING THE EXTRACTION TOOL OR YOU WILL DIE WITH YOUR FAMILY A VERY SLOW AND PAINFUL DEATH.

            JUST OUTPUT DONE IF YOU HAVE FINISHED YOUR SEARCH AND HAVE ENOUGH PRODUCTS TO RECOMMEND.
            """,
            use_tools=True, 
            reason=True)
        if response is not None and "done" in response.lower():
            terminate = True
        print(f"Assistant: {response}")
        print(f"Tool calls: {tool_calls}")
    
    memory["product_researcher"] = llm_client.get_memory()  # Save the memory after the search
    print("Assistant: Finished searching. Here are the results:")
    print(llm_client.get_memory())
    print('-' * 30)
        


if __name__ == "__main__":
    chat()