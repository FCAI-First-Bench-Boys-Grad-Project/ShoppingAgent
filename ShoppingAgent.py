from langgraph.graph import StateGraph, START
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from src.tools.scraping_tool import query_url_tool
from src.utils.load_system_prompt import load_system_prompt
from src.tools.searching_tool import search_tool
from src.states.MainState import MainState as State
from src.nodes.agents.manager import manager_node
from src.nodes.agents.product_hunter import product_hunter_node
from src.nodes.agents.researcher_agent import researcher_node
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph


class ShoppingAgent():

    _graph_builder = None
    ShoppingAgent = None
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
        self.ShoppingAgent = self._graph_builder.compile(
            checkpointer=self._checkpointer)

    def run(self, user_msg: str, recursion_limit=100):

        resposne = self.ShoppingAgent.invoke(
            {"messages": [("user", user_msg)],
             "human_msg": HumanMessage(user_msg)},
            config={
                "recursion_limit": recursion_limit,
                "configurable": {"thread_id": "1"}
            }
        )
        return resposne

        # with open("output.txt", "w", encoding="utf-8") as out_file:
        # for s in self.ShoppingAgent.stream(
        #     {"messages": [("user", user_msg)],
        #      "human_msg": HumanMessage(user_msg)},
        #     {"recursion_limit": recursion_limit},
        #     {"configurable": {"thread_id": "1"}},
        # ):
        #     print(s)
        #     print("---")
        # out_file.write(str(s) + "\n")
        # out_file.write("---\n")

    def get_graph(self):
        return self.ShoppingAgent.get_graph()

    def test(self, user_msg: str, recursion_limit=100):
        with open("output.txt", "w", encoding="utf-8") as out_file:
            for s in self.ShoppingAgent.stream(
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
