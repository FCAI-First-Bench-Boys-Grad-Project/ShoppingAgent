from llama_index.llms.gemini import Gemini

def create_gemini():
    return Gemini(model="models/gemini-2.0-flash")