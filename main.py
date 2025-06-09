from src.agents.manager import manager_agent
from src.agents.product_hunter import product_hunter_agnet
from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent
from llama_index.core.workflow import Context
import asyncio

async def main():

    workflow = AgentWorkflow(
        agents=[manager_agent, product_hunter_agnet],
        root_agent="manager_agent"
    )

    # To keep memory
    ctx = Context(workflow)

    response = await workflow.run(
        user_msg="I want to build a Gaming PC for around 1000 Dollars, I don't care about looks or RGB but I care about performance, I want the greatest performance for gaming on 1080p with these 1000 dollars, also the pc should have at least 16 GBs of ram and 1TB ssd , I live in Texas. Can you please give me the pc parts links I should buy online to build that pc ?",
        ctx=ctx
    )



if __name__ == "__main__":
    asyncio.run(main())
