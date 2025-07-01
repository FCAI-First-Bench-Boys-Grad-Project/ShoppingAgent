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
# from src.nodes.ask_user import ask_user
# from src.nodes.clear_memory import clear_memory
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph


class ShoppingAgent():

    _graph_builder = None
    _ShoppingAgent = None
    _checkpointer = InMemorySaver()
    _workers = {
        "researcher_agent": researcher_node,
        "product_hunter_agent": product_hunter_node,
        # "ask_user": ask_user,
        # "clear_memory": clear_memory
    }

    def __init__(self):
        self._graph_builder = StateGraph(State)
        for name, func in self._workers.items():
            self._graph_builder.add_node(name, func)
        self._graph_builder.add_node("manager", manager_node)

        self._graph_builder.add_edge(START, "manager")
        self._ShoppingAgent = self._graph_builder.compile(
            checkpointer=self._checkpointer)

    def run(self, user_msg: str, recursion_limit=100):
        # with open("output.txt", "w", encoding="utf-8") as out_file:
        for s in self._ShoppingAgent.stream(
            {"messages": [("user", user_msg)],
             "human_msg": HumanMessage(user_msg)},
            {"recursion_limit": recursion_limit},
            {"configurable": {"thread_id": "1"}},
        ):
            print(s)
            print("---")
            # out_file.write(str(s) + "\n")
            # out_file.write("---\n")

    def get_graph(self):
        return self._ShoppingAgent.get_graph()

    def test(self, user_msg: str, recursion_limit=100):
        with open("output.txt", "w", encoding="utf-8") as out_file:
            for s in self._ShoppingAgent.stream(
                {"messages": [("user", user_msg)],
                 "human_msg": HumanMessage(user_msg)},
                config={
                    "recursion_limit": recursion_limit,
                    "configurable": {"thread_id": "1"}
                }

            ):
                print(s)
                print("---")
                out_file.write(str(s) + "\n")
                out_file.write("---\n")
