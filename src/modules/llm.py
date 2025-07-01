from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_nvidia_ai_endpoints import ChatNVIDIA


llm_name = "gemini-2.5-flash"  # or "gemini-1.5-pro" or "gemini-1.5-flash"

model = ChatGoogleGenerativeAI(
    model=llm_name,
    temperature=0.5,
)


# model = ChatNVIDIA(model="qwen/qwen3-235b-a22b", max_tokens=8192)
