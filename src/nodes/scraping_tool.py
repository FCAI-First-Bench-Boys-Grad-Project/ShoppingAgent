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
from src.tools.scraping_tool import query_url_tool


def scraping_tool(state: State):
    links = state["links"][0] if "links" in state else []
    for link in links:
        link.description = query_url_tool(
            {"data_schema": state['scraping_schema'], "url": link.link})
    res = [link for link in links]
    return {"links": [res], "isScraped": True, "next_node": state['last_agent'], 'last_agent': state['last_agent']}
