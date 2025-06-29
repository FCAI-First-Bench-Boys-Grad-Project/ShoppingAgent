from src.states.MainState import MainState as State
from src.modules.Link import Link
from src.tools.searching_tool import search_tool


def searching_tool(state: State):
    query = state["messages"][-1].content if state["messages"] else ""
    res = search_tool({"query": query})
    links = [Link(link=link, description="") for link in res]
    return {"links": links, "isScraped": False, "next_node": state['last_agent'], 'last_agent': state['last_agent']}
