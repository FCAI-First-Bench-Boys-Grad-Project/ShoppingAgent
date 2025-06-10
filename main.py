# libraries imports
import yaml
import asyncio
from llama_index.core.workflow import Context
from src.llms.gemini_2_flash import create_gemini
from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent.workflow import AgentWorkflow, ToolCallResult, AgentStream


# Custom imports
from src.tools.web_search import search_tool
from src.tools.visit_webpage import visit_webpage
from dotenv import load_dotenv
import os

# Load environment variables

# Load environment variables from .env file
load_dotenv()

async def main():

    llm = create_gemini()

    # Load configuration from YAML file

    def load_config(file_path):
        """Load configuration from a YAML file."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return {}

    # Load configuration
    config = load_config('src/agents/prompts.yaml')

    # TODO: Impelment
    manager_agent = ReActAgent(
        name=config["manager_agent"]["name"],
        description=config["manager_agent"]["description"],
        system_prompt=config["manager_agent"]["system_prompt"],
        tools=[],
        llm=llm,
    )

    product_hunter_agent = ReActAgent(
        name=config["product_hunter_agent"]["name"],
        description=config["product_hunter_agent"]["description"],
        system_prompt=config["product_hunter_agent"]["system_prompt"],
        tools=[search_tool, visit_webpage],
        llm=llm,
    )

    trivial_search_agent = ReActAgent(
        name=config["trivial_search_agent"]["name"],
        description=config["trivial_search_agent"]["description"],
        system_prompt=config["trivial_search_agent"]["system_prompt"],
        tools=[search_tool, visit_webpage],
        llm=llm,
    )

    shopping_researcher_agent = ReActAgent(
        name=config["shopping_researcher_agent"]["name"],
        description=config["shopping_researcher_agent"]["description"],
        system_prompt=config["shopping_researcher_agent"]["system_prompt"],
        tools=[search_tool, visit_webpage],
        llm=llm,
    )

    product_investigator_agent = ReActAgent(
        name=config["product_investigator_agent"]["name"],
        description=config["product_investigator_agent"]["description"],
        system_prompt=config["product_investigator_agent"]["system_prompt"],
        tools=[search_tool, visit_webpage],
        llm=llm,
    )


    workflow = AgentWorkflow(
        #TODO: Add the rest of the agents & Make their tools
        agents=[manager_agent, shopping_researcher_agent , product_hunter_agent, product_investigator_agent, trivial_search_agent],
        root_agent="manager_agent"
    )

    # To keep memory
    ctx = Context(workflow)

    prompt = "I want to build a Gaming PC for around 50k EGP, I don't care about looks or RGB but I care about performance, I want the greatest performance for gaming on 1080p with these 1000 dollars, also the pc should have at least 16 GBs of ram and 1TB ssd , I live in Egypt. Can you please give me the pc parts links I should buy online to build that pc ?"

    prompt = "I am having a wedding next week, i want to buy a wedding dress for my wife, i want it to be white and elegant, i want it to be around 10 EGP, can you please give me the links of the dresses that fit this description ?"

    prompt = "I want a mate to have sex with. my budget is 1$"

    prompt = "I want to buy a wedding suit with tie and everything with a maximum budget of 30k EGP in Cairo."

    handler = workflow.run(
        user_msg=prompt,
        ctx=ctx
    )

    with open("agent_output.txt", "a", encoding="utf-8") as f:
        async for ev in handler.stream_events():
            agent_info = f"[{getattr(ev, 'name', 'unknown agent')}] "
            if isinstance(ev, ToolCallResult):
                line = f"\n{agent_info}Called tool: {ev.tool_name} {ev.tool_kwargs} => {ev.tool_output}\n"
                print(line, end="")
                f.write(line)
            elif isinstance(ev, AgentStream):  # showing the thought process
                delta_line = f"{agent_info}{ev.delta}"
                print(delta_line, end="", flush=True)
                f.write(delta_line)

    # async for ev in handler.stream_events():
    # if isinstance(ev, ToolCallResult):
    #     print("")
    #     print("Called tool: ", ev.tool_name, ev.tool_kwargs, "=>", ev.tool_output)
    #     await print(f"\nCalled tool: {ev.tool_name} {ev.tool_kwargs} => {ev.tool_output}\n")
    # elif isinstance(ev, AgentStream):  # showing the thought process
    #     print(ev.delta, end="", flush=True)
    #     await print(ev.delta)
    
    resp = await handler
    
    print(resp)

if __name__ == "__main__":
    asyncio.run(main())
