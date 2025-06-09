# libraries imports
import yaml
import asyncio
from llama_index.core.workflow import Context
from llms.gemini_2_flash import create_gemini
from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent

# Custom imports
from tools.web_search import search_tool
from tools.visit_webpage import visit_webpage

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

    product_hunter_agnet = ReActAgent(
        name=config["product_hunter_agnet"]["name"],
        description=config["product_hunter_agnet"]["description"],
        system_prompt=config["product_hunter_agnet"]["system_prompt"],
        tools=[search_tool, visit_webpage],
        llm=llm,
    )

    trivial_search_agnet = ReActAgent(
        name=config["trivial_search_agnet"]["name"],
        description=config["trivial_search_agnet"]["description"],
        system_prompt=config["trivial_search_agnet"]["system_prompt"],
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
        agents=[manager_agent, shopping_researcher_agent , product_hunter_agnet, product_investigator_agent, trivial_search_agnet],
        root_agent="manager_agent"
    )

    # To keep memory
    ctx = Context(workflow)

    # Create a handler to print agent and tool calls
    def workflow_handler(event_type, payload):
        if event_type == "agent_step":
            agent_name = payload.get("agent_name", "Unknown agent")
            thought = payload.get("thought", "No thought provided")
            print(f"\n🤖 AGENT: {agent_name}")
            print(f"💭 THOUGHT: {thought}")
        elif event_type == "tool_call":
            tool_name = payload.get("tool", {}).get("name", "Unknown tool")
            tool_input = payload.get("tool_input", "No input")
            print(f"\n🔧 TOOL CALL: {tool_name}")
            print(f"📥 INPUT: {tool_input}")
        elif event_type == "tool_result":
            result = payload.get("result", "No result")
            print(f"📤 RESULT: {result[:200]}..." if len(str(result)) > 200 else f"📤 RESULT: {result}")

    # Add the handler to the workflow
    workflow.add_handler(workflow_handler)

    # Run the workflow
    response = await workflow.run(
        user_msg="I want to build a Gaming PC for around 1000 Dollars, I don't care about looks or RGB but I care about performance, I want the greatest performance for gaming on 1080p with these 1000 dollars, also the pc should have at least 16 GBs of ram and 1TB ssd , I live in Texas. Can you please give me the pc parts links I should buy online to build that pc ?",
        ctx=ctx
    )
    
    # Print the final response
    print("\n📝 FINAL RESPONSE:")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
