from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent

from llms.gemini_2_flash import create_gemini

# TODO: shuold not make new llm object for every agent, should use same object.
llm = create_gemini()

# TODO: Implement
product_hunter_agnet = ReActAgent(
    name="product_hunter",
    description="",
    system_prompt="",
    tools=[],
    llm=llm
)
