from dotenv import load_dotenv
from typing import Annotated,  Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
import getpass
from src.nodes.agents.manager import manager_agent
from src.nodes.agents.product_hunter import product_hunter_agent
from src.nodes.agents.evaluator import evaluator_agent
from src.nodes.agents.researcher_agent import researcher_agent
import langsmith
from src.states.MainState import MainState as State
from src.nodes.ask_human import ask_human
from src.nodes.searching_tool import searching_tool
from src.nodes.scraping_tool import scraping_tool
from IPython.display import Image

# THis is my branch now abo abdo 
load_dotenv()


graph_builder = StateGraph(State)


def router(state: State) -> str:
    next_node = state["next_node"]
    print(next_node)
    if next_node:
        return next_node
    else:
        return "end"


graph_builder.add_node("manager", manager_agent)
graph_builder.add_node("product_hunter_agent", product_hunter_agent)
graph_builder.add_node("researcher_agent", researcher_agent)
graph_builder.add_node("evaluator_agent", evaluator_agent)
graph_builder.add_node("ask_human", ask_human)
graph_builder.add_node("searching_tool", searching_tool)
graph_builder.add_node("scraping_tool", scraping_tool)

graph_builder.set_entry_point("manager")


graph_builder.add_conditional_edges("manager", router,
                                    {"product_hunter_agent": "product_hunter_agent",
                                        "researcher_agent": "researcher_agent",
                                        "evaluator_agent": "evaluator_agent",
                                        "ask_human": "ask_human",
                                        "end": END
                                     })

graph_builder.add_conditional_edges("product_hunter_agent", router,
                                    {"searching_tool": "searching_tool",
                                        "scraping_tool": "scraping_tool",
                                        "manager": "manager"
                                     })

graph_builder.add_conditional_edges("researcher_agent", router,
                                    {"searching_tool": "searching_tool",
                                        "scraping_tool": "scraping_tool",
                                        "manager": "manager"
                                     })
graph_builder.add_conditional_edges("searching_tool", router,
                                    {"product_hunter_agent": "product_hunter_agent",
                                     "researcher_agent": "researcher_agent"
                                     })
graph_builder.add_conditional_edges("scraping_tool", router,
                                    {"product_hunter_agent": "product_hunter_agent",
                                        "researcher_agent": "researcher_agent",
                                     })

# graph_builder.add_edge("researcher_agent", "manager")
# graph_builder.add_edge("product_hunter_agent", "manager")
graph_builder.add_edge("evaluator_agent", "manager")
graph_builder.add_edge("ask_human", "manager")


graph_builder.set_finish_point("manager")
graph = graph_builder.compile()
with open("graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())
print("Graph image saved as graph.png")

user_input = "i want to buy a phone with a $300 budget, i don't have any specific specifications, but i want it to be a good phone. can you help me find one?"
# user_input = "i want something"
# user_input = "I want to build a gaming PC with under 1000 USD"
state = graph.invoke({"messages": [HumanMessage(user_input)],
                     "isHuman": True, "next_node": "manager", "final_response": "", "user_messages": [HumanMessage(user_input)]})

with open("output.log", "w") as f:
    f.write(state["final_response"])

print(state["final_response"])
