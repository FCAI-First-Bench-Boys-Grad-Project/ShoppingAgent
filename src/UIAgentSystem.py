# libraries imports
import threading
from queue import Queue
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager

import yaml
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from llama_index.core.workflow import Context
from llms.gemini_2_flash import create_gemini
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent import AgentRunner, ReActAgent
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent
from llama_index.core.agent.workflow import AgentWorkflow, ToolCallResult, AgentStream

# Custom Imports
from tools.web_search import search_tool
from tools.visit_webpage import visit_webpage
from tools.query_on_url import Get_info_from_url_tool
from GradioCallbackHandler import GradioCallbackHandler


# Load Environmnet Variables
load_dotenv()


class UIAgentSystem:
    def __init__(self):
        """Initializes the entire multi-agent system."""
        # 1. Create the communication queue
        self.event_queue = Queue()

        # 2. Create our custom callback handler
        self.gradio_callback_handler = GradioCallbackHandler(self.event_queue)

        # 3. Set up the global callback manager
        # LlamaIndex will use this manager for all subsequent objects.
        Settings.callback_manager = CallbackManager([self.gradio_callback_handler])
        Settings.llm = create_gemini() # Also good practice to set this globally

        def load_config(file_path):
            """Load configuration from a YAML file."""
            try:
                with open(file_path, 'r') as file:
                    return yaml.safe_load(file)
            except Exception as e:
                print(f"Error loading config file: {e}")
                return {}

        # Load configuration
        config = load_config('agents/prompts.yaml')

        # 4. Create the agents (they will automatically pick up the global callback manager)
        # Re-initialize them here so they inherit the new settings
        product_hunter_agent = ReActAgent(
            name=config["product_hunter_agent"]["name"],
            description=config["product_hunter_agent"]["description"],
            system_prompt=config["product_hunter_agent"]["system_prompt"],
            tools=[search_tool, visit_webpage, Get_info_from_url_tool],
            llm=Settings.llm,
            callback_manager=self.gradio_callback_handler,
        )

        trivial_search_agent = ReActAgent(
            name=config["trivial_search_agent"]["name"],
            description=config["trivial_search_agent"]["description"],
            system_prompt=config["trivial_search_agent"]["system_prompt"],
            tools=[search_tool, visit_webpage, Get_info_from_url_tool],
            llm=Settings.llm,
            callback_manager=self.gradio_callback_handler,
        )

        shopping_researcher_agent = ReActAgent(
            name=config["shopping_researcher_agent"]["name"],
            description=config["shopping_researcher_agent"]["description"],
            system_prompt=config["shopping_researcher_agent"]["system_prompt"],
            tools=[search_tool, visit_webpage, Get_info_from_url_tool],
            llm=Settings.llm,
            callback_manager=self.gradio_callback_handler,
        )

        product_investigator_agent = ReActAgent(
            name=config["product_investigator_agent"]["name"],
            description=config["product_investigator_agent"]["description"],
            system_prompt=config["product_investigator_agent"]["system_prompt"],
            tools=[search_tool, visit_webpage, Get_info_from_url_tool],
            llm=Settings.llm,
            callback_manager=self.gradio_callback_handler,
        )

        # 5. Create the orchestrator
        # self.agent_runner = AgentRunner(
        #     agents=[self.math_agent, self.text_agent],
        #     callback_manager=Settings.callback_manager,
        #     system_prompt=config["manager_agent"]["system_prompt"]
        # )

        self.workflow = AgentWorkflow(
            agents=[]
        )

    def _run_agent_in_thread(self, query: str):
        """
        The target function for our thread. Runs the agent and puts the
        final response and a sentinel value into the queue.
        """
        final_response = self.agent_runner.chat(query)
        # Put the final answer into the queue
        self.event_queue.put({"type": "final_answer", "content": str(final_response)})
        # Put a "sentinel" value to signal the end of the stream
        self.event_queue.put(None)

    def stream_agent_responses(self, query: str):
        """
        This is the main method Gradio will call.
        It starts the agent in a background thread and yields messages from the queue.
        """
        # Start the agent in a separate thread to not block the Gradio UI
        thread = threading.Thread(target=self._run_agent_in_thread, args=(query,))
        thread.start()

        # Yield messages from the queue as they come in
        while True:
            # Wait for a message from the queue
            message = self.event_queue.get()

            if message is None: # Check for the sentinel value
                break

            yield message