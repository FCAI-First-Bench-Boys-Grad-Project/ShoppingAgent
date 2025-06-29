from src.states.MainState import MainState as State
from src.tools.scraping_tool import query_url_tool


def scraping_tool(state: State):
    links = state["links"][0] if "links" in state else []
    for link in links:
        link.description = query_url_tool(
            {"data_schema": state['scraping_schema'], "url": link.link})
    res = [link for link in links]
    return {"links": [res], "isScraped": True, "next_node": state['last_agent'], 'last_agent': state['last_agent']}
