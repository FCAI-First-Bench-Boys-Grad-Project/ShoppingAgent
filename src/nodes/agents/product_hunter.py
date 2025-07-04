from typing_extensions import Literal

from langchain.agents import create_tool_calling_agent

from langchain_core.messages import HumanMessage

from src.states.MainState import MainState as State
from src.utils.load_system_prompt import load_system_prompt
from src.tools.scraping_tool import query_url_tool
from src.tools.searching_tool import search_tool
from src.modules.llm import model
from langgraph.types import Command
from time import sleep
from langgraph.prebuilt import create_react_agent
from src.modules.llm import model
from langgraph.prebuilt import create_react_agent


tools = [search_tool, query_url_tool]


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
