from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv 
import os

load_dotenv()
llm_name = "gemini-2.0-flash"  # or "gemini-1.5-pro" or "gemini-1.5-flash"

model = ChatGoogleGenerativeAI(
    model=llm_name,
    temperature=0.5,
    google_api_key=os.getenv("GEMINI_API_KEY", ""),  # Set your API key here
)
