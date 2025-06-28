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
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.states.MainState import MainState as State

from src.utils.load_system_prompt import load_system_prompt
from src.modules.Link import Link

from src.tools.searching_tool import search_tool


def searching_tool(state: State):
    query = state["messages"][-1].content if state["messages"] else ""
    res = search_tool({"query": query})
    links = [Link(link=link, description="") for link in res]
    return {"links": links, "isScraped": False, "next_node": state['last_agent'], 'last_agent': state['last_agent']}
