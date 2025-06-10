
# libraries imports
import yaml
import asyncio
from datetime import datetime
from llama_index.core.workflow import Context
from src.llms.gemini_2_flash import create_gemini
from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent.workflow import AgentWorkflow, ToolCallResult, AgentStream


# Custom imports
from src.tools.web_search import search_tool
from src.tools.visit_webpage import visit_webpage
from src.tools.query_on_url import Get_info_from_url_tool
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class CustomDebugHandler(LlamaDebugHandler):
    """Custom debug handler for better traceability"""

    def __init__(self):
        super().__init__()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def on_event_start(self, event_type, payload=None, event_id="", **kwargs):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n🚀 [{timestamp}] Event Started: {event_type}")
        if payload:
            print(f"   📋 Payload: {payload}")
        super().on_event_start(event_type, payload, event_id, **kwargs)

    def on_event_end(self, event_type, payload=None, event_id="", **kwargs):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n✅ [{timestamp}] Event Completed: {event_type}")
        super().on_event_end(event_type, payload, event_id, **kwargs)


def create_callback_manager():
    """Create a callback manager with custom handlers"""
    debug_handler = CustomDebugHandler()
    callback_manager = CallbackManager([debug_handler])
    return callback_manager


def get_agent_name_enhanced(ev, workflow):
    """Enhanced agent name detection with multiple fallback strategies"""

    # Strategy 1: Direct attribute check
    for attr in ['agent_name', 'name', 'sender', 'agent']:
        if hasattr(ev, attr):
            value = getattr(ev, attr)
            if value and isinstance(value, str):
                return value

    # Strategy 2: Check source object
    if hasattr(ev, 'source'):
        source = ev.source
        for attr in ['agent_name', 'name', 'id']:
            if hasattr(source, attr):
                value = getattr(source, attr)
                if value and isinstance(value, str):
                    return value

    # Strategy 3: Check workflow context or metadata
    if hasattr(ev, 'metadata') and ev.metadata:
        if 'agent_name' in ev.metadata:
            return ev.metadata['agent_name']

    # Strategy 4: Try to infer from workflow state
    if hasattr(workflow, '_current_agent') and workflow._current_agent:
        return workflow._current_agent

    # Strategy 5: Check event type patterns
    event_type = type(ev).__name__
    if 'Agent' in event_type:
        return f"Agent_{event_type}"

    return "UnknownAgent"


def format_output_message(agent_name, message_type, content, timestamp=None):
    """Format output messages consistently"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M:%S")

    separator = "=" * 60
    header = f"[{timestamp}] {agent_name} - {message_type}"

    return f"\n{separator}\n{header}\n{separator}\n{content}\n{separator}\n"


def load_config(file_path):
    """Load configuration from a YAML file."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}


class ShoppingAgent:
    """Base class for shopping agents with common functionality"""

    def __init__(self, llm):
        self.callback_manager = create_callback_manager()
        self.llm = llm
        self.callback_manager = create_callback_manager()
        self.config = load_config('src/agents/prompts.yaml')
        self.chat_history = []
        self.manager_agent = ReActAgent(
            name=self.config["manager_agent"]["name"],
            description=self.config["manager_agent"]["description"],
            system_prompt=self.config["manager_agent"]["system_prompt"],
            tools=[],
            llm=llm,
            callback_manager=self.callback_manager,
        )
        self.product_hunter_agent = ReActAgent(
            name=self.config["product_hunter_agent"]["name"],
            description=self.config["product_hunter_agent"]["description"],
            system_prompt=self.config["product_hunter_agent"]["system_prompt"],
            # tools=[search_tool, visit_webpage],
            tools=[search_tool, visit_webpage, Get_info_from_url_tool],
            llm=llm,
            callback_manager=self.callback_manager,
        )

        self.trivial_search_agent = ReActAgent(
            name=self.config["trivial_search_agent"]["name"],
            description=self.config["trivial_search_agent"]["description"],
            system_prompt=self.config["trivial_search_agent"]["system_prompt"],
            # tools=[search_tool, visit_webpage],

            tools=[search_tool, visit_webpage, Get_info_from_url_tool],
            llm=llm,
            callback_manager=self.callback_manager,
        )

        self.shopping_researcher_agent = ReActAgent(
            name=self.config["shopping_researcher_agent"]["name"],
            description=self.config["shopping_researcher_agent"]["description"],
            system_prompt=self.config["shopping_researcher_agent"]["system_prompt"],
            # tools=[search_tool, visit_webpage],
            tools=[search_tool, visit_webpage, Get_info_from_url_tool],
            llm=llm,
            callback_manager=self.callback_manager,
        )

        self.product_investigator_agent = ReActAgent(
            name=self.config["product_investigator_agent"]["name"],
            description=self.config["product_investigator_agent"]["description"],
            system_prompt=self.config["product_investigator_agent"]["system_prompt"],
            # tools=[search_tool, visit_webpage],
            tools=[search_tool, visit_webpage, Get_info_from_url_tool],
            llm=llm,
            callback_manager=self.callback_manager,
        )
        self.workflow = AgentWorkflow(
            agents=[self.manager_agent, self.shopping_researcher_agent, self.product_hunter_agent,
                    self.product_investigator_agent, self.trivial_search_agent],
            root_agent="manager_agent",
        )
        self.ctx = Context(self.workflow)

        if hasattr(llm, 'callback_manager'):
            self.llm.callback_manager = self.callback_manager

    async def query(self, prompt):
        """
        Run the shopping assistant workflow and maintain chat history.

        Args:
            prompt (str): The user's input query

        Returns:
            str: The agent's response
        """
        # Add user prompt to chat history
        self.chat_history.append({
            "role": "user",
            "content": prompt,
        })

        # Update context with current chat history
        self.ctx.chat_history = self.chat_history

        # Run the workflow
        resp = await self.workflow.run(
            user_msg=prompt,
            ctx=self.ctx
        )

        # Add agent response to chat history
        self.chat_history.append({
            "role": "assistant",
            "content": str(resp),
        })

        # Update context again with new chat history
        self.ctx.chat_history = self.chat_history

        return resp


# async def main():
#     prompt = "Find the best smartphone under $500 with good camera quality."
#     shopping_agent = ShoppingAgent(
#         llm=create_gemini(),
#     )
#     print(await shopping_agent.query(prompt))

# if __name__ == "__main__":
#     asyncio.run(main())
