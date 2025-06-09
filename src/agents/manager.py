from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent

from llms.gemini_2_flash import create_gemini


llm = create_gemini()

# TODO: Impelment
manager_agent = ReActAgent(
    name="manager_agent",
    description="",
    system_prompt="",
    tools=[],
    llm=llm,
)


