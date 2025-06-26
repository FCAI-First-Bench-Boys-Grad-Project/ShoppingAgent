from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import yaml
import uuid
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from src.states.MainState import MainState as State

from src.utils.load_system_prompt import load_system_prompt


# Define the function that calls the model
def ask_human(state: State):
    user_message = ''
    cnt = 0
    while (not user_message and cnt < 3):
        user_message = input("Please provide your input: ")
        cnt += 1

    return {"messages": [HumanMessage(user_message)], "isHuman": True}
