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

tools = []

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.5,
)

system_prompt = load_system_prompt("researcher_agent")


# Define the function that calls the model
def researcher_agent(state: State):

    response = llm.invoke([
        SystemMessage(
            content=system_prompt
        ),
        HumanMessage(
            content=state["messages"][-1].content if state["messages"] else ""
        ),
    ])
    return {"messages": [response], "isHuman": False, "next_node": "researcher_agent"}
