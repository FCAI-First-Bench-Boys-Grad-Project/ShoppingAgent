from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_core.messages import HumanMessage
from src.states.MainState import MainState as State
from src.utils.load_system_prompt import load_system_prompt
from src.modules.llm import model
from langgraph.types import Command
from time import sleep
from langgraph.prebuilt import create_react_agent
from src.modules.llm import model
from src.tools.scraping_tool import query_url_tool
from src.tools.searching_tool import search_tool


tools = [search_tool, query_url_tool]

researcher_agent = create_react_agent(
    model=model,
    tools=tools,
    prompt=load_system_prompt("researcher_agent"),
    name="researcher_agent",
)


def researcher_node(state: State) -> Command[Literal["manager"]]:
    sleep(1)
    result = researcher_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"]
                             [-1].content, name="researcher")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="manager",  # Changed to researcher_agent to match the agent name
    )
