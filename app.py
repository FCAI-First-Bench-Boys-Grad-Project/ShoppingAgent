from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel,load_tool,tool
import datetime
import requests
import pytz
import yaml
from tools.final_answer import FinalAnswerTool
from tools.visit_webpage import VisitWebpageTool
from tools.web_search import DuckDuckGoSearchTool

from Gradio_UI import GradioUI


import google.generativeai as genai

class GeminiApiModel:
    def __init__(self, api_key, model_name="gemini-pro", max_tokens=2048, temperature=0.1):
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def __call__(self, prompt, **kwargs):
        response = self.model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": self.max_tokens,
                "temperature": self.temperature,
            }
        )
        # Gemini's response is in response.text
        return response.text

# @tool
# def get_current_weather(location: str, forecast_days: int = 1) -> str:
#     """
#     Fetches the current weather and optionally forecast for a given location.
    
#     Args:
#         location (str): The name of the city/location to get the weather for.
#         forecast_days (int): Number of days to get forecast for (default is 1).
        
#     Returns:
#         str: A string containing the current weather and temperature in the location.
#     """
#     base_url = "http://api.weatherapi.com/v1/current.json"
#     params = {
#         "key": WEATHER_API_KEY,
#         "q": location,
#         "days": forecast_days
#     }

#     try:
#         response = requests.get(base_url, params=params)
#         data = response.json()
        
#         if "error" in data:
#             return f"Error fetching weather data: {data['error']['message']}"


#         current_temp = data["current"]["temp_c"]
#         condition = data["current"]["condition"]["text"]
#         city = data["location"]["name"]
#         country = data["location"]["country"]

#         result = (
#             f"The current weather in {city}, {country} is {condition}. "
#             f"The temperature is {current_temp}°C."
#         )
#         return result
    
#     except Exception as e:
#         return f"Failed to retrieve weather information: {e}"

# @tool
# def get_current_time_in_timezone(timezone: str) -> str:
#     """A tool that fetches the current local time in a specified timezone.
#     Args:
#         timezone: A string representing a valid timezone (e.g., 'America/New_York').
#     """
#     try:
#         # Create timezone object
#         tz = pytz.timezone(timezone)
#         # Get current time in that timezone
#         local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
#         return f"The current local time in {timezone} is: {local_time}"
#     except Exception as e:
#         return f"Error fetching time for timezone '{timezone}': {str(e)}"


final_answer = FinalAnswerTool()

# If the agent does not answer, the model is overloaded, please use another model or the following Hugging Face Endpoint that also contains qwen2.5 coder:
# model_id='https://pflgm2locj2t89co.us-east-1.aws.endpoints.huggingface.cloud' 

# model = HfApiModel(
# max_tokens=2096,
# temperature=0.1,
# model_id='Qwen/Qwen2.5-Coder-32B-Instruct',# it is possible that this model may be overloaded
# custom_role_conversions=None,
# )

from dotenv import load_dotenv
import os
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


model = GeminiApiModel(
    api_key=GEMINI_API_KEY,
    max_tokens=2096,
    temperature=0.1,
    model_name="gemini-2.0-flash",  # or another Gemini model if available
)


# Import tool from Hub
image_generation_tool = load_tool("agents-course/text-to-image", trust_remote_code=True)

with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)
    
agent = CodeAgent(
    model=model,
    tools=[final_answer, DuckDuckGoSearchTool(), VisitWebpageTool()], ## add your tools here (don't remove final answer)
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates
)


GradioUI(agent).launch()