from langchain_google_genai import ChatGoogleGenerativeAI


llm_name = "gemini-2.0-flash"  # or "gemini-1.5-pro" or "gemini-1.5-flash"

model = ChatGoogleGenerativeAI(
    model=llm_name,
    temperature=0.5,
)
