from typing_extensions import Literal
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
import yaml
import uuid
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
# from src.states.ProductHunterState import ProductHunterState as State
# from src.states.MainState import MainState as State
from src.states.MainState import MainState as State
from src.utils.load_system_prompt import load_system_prompt
from src.tools.scraping_tool import query_url_tool
from src.tools.searching_tool import search_tool
from src.modules.llm import model
from langgraph.types import Command
from time import sleep, time
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent
from src.modules.llm import model

from langgraph.prebuilt import create_react_agent
tools = [query_url_tool, search_tool]


product_hunter_agent = create_react_agent(
    model=model,
    tools=tools,
    prompt=load_system_prompt("product_hunter_agent"),
    name="product_hunter_agent",
)


def product_hunter_node(state: State) -> Command[Literal["manager"]]:
    sleep(1)
    result = product_hunter_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"]
                             [-1].content, name="product hunter")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="manager",  # Changed to researcher_agent to match the agent name
    )
