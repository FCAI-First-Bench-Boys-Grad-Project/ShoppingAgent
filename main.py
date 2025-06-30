from time import sleep, time
from langchain_google_genai import ChatGoogleGenerativeAI
from IPython.display import Image, display
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from typing import List, Optional, Literal, TypedDict
from langchain_core.language_models.chat_models import BaseChatModel

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, trim_messages, AIMessage
from typing import Annotated, List

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.tools.scraping_tool import query_url_tool
from src.utils.load_system_prompt import load_system_prompt
from src.tools.searching_tool import search_tool

from src.states.MainState import MainState as State
from src.nodes.agents.manager import manager_node
from src.nodes.agents.product_hunter import product_hunter_node
from src.nodes.agents.researcher_agent import researcher_node
from src.nodes.ask_human import ask_human


load_dotenv()


research_builder = StateGraph(State)
research_builder.add_node("manager", manager_node)
research_builder.add_node("researcher_agent", researcher_node)
research_builder.add_node("product_hunter_agent", product_hunter_node)
research_builder.add_node("ask_human", ask_human)

research_builder.add_edge(START, "manager")
research_graph = research_builder.compile()

with open("graph2.png", "wb") as f:
    f.write(research_graph.get_graph().draw_mermaid_png())
print("Graph image saved as graph.png")

user_msg = "i want to build a pc and my budget is 1000 USD"

with open("output.txt", "w", encoding="utf-8") as out_file:
    for s in research_graph.stream(
        {"messages": [("user", user_msg)]},
        {"recursion_limit": 100},
    ):
        print(s)
        print("---")
        out_file.write(str(s) + "\n")
        out_file.write("---\n")
