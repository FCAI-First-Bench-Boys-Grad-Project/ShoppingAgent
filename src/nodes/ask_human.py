from typing import Literal
from langchain.agents import create_tool_calling_agent
from langchain_core.messages import HumanMessage
from src.states.MainState import MainState as State

from src.utils.load_system_prompt import load_system_prompt
from langgraph.types import Command


def ask_human(state: State) -> Command[Literal["manager"]]:
    result = str(input("Your respond: "))
    # Here we assume the user will provide a response that the
    return Command(
        update={
            "messages": [
                HumanMessage(content=result, name="user")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="manager",  # Changed to researcher_agent to match the agent name
    )
