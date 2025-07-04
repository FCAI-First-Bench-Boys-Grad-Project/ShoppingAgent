from langchain_google_genai import ChatGoogleGenerativeAI
import os
from typing import Optional
from langchain_core.utils.utils import secret_from_env
from langchain_openai import ChatOpenAI
from pydantic import Field, SecretStr
# from langchain_nvidia_ai_endpoints import ChatNVIDIA


from langchain_openai import ChatOpenAI
from os import getenv
from dotenv import load_dotenv

load_dotenv()
# or "gemini-1.5-pro" or "gemini-1.5-flash"


class ChatOpenRouter(ChatOpenAI):
    def __init__(self, openai_api_key: Optional[str] = None, **kwargs):
        openai_api_key = os.environ.get("OPENROUTER_API_KEY")
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            api_key=openai_api_key,
            **kwargs
        )


# llm_name = "google/gemini-2.5-flash"
llm_name = "google/gemini-2.5-pro"
llm_name = "google/gemini-2.5-pro"


model = ChatOpenRouter(model=llm_name, temperature=0.1)
# llm_name = "gemini-2.5-flash"  # or "gemini-1.5-pro" or "gemini-1.5-flash"


# model = ChatOpenRouter(
#     model_name="llm_name",
#     temperature=0.5
# )


# model = ChatGoogleGenerativeAI(
#     model=llm_name,
#     temperature=0.5,
# )


# model = ChatNVIDIA(model="qwen/qwen3-235b-a22b", max_tokens=8192)
