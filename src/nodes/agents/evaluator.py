from langchain_core.messages import HumanMessage, SystemMessage
from src.states.MainState import MainState as State
from src.modules.llm import model
from src.utils.load_system_prompt import load_system_prompt

tools = []

llm = model

system_prompt = load_system_prompt("evaluator_agent")


# Define the function that calls the model
def evaluator_agent(state: State):

    response = llm.invoke([
        SystemMessage(
            content=system_prompt
        ),
        HumanMessage(
            content=state["messages"][-1].content if state["messages"] else ""
        ),
    ])
    return {"messages": [HumanMessage(response.content)],
            "isHuman": False,
            "next_node": "manager",
            "last_agent": "evaluator_agent"
            }
