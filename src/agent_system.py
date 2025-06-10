# agent_system.py

import yaml
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from llama_index.core.workflow import Context
from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent

from llama_index.core.agent.workflow import ToolCallResult, AgentStream
# from llama_index.core.agent.runner.base import AgentStream
import os
# Custom imports (ensure these paths are correct and files exist)
from llms.gemini_2_flash import create_gemini
from tools.web_search import search_tool
from tools.visit_webpage import visit_webpage
from tools.query_on_url import Get_info_from_url_tool

# Load environment variables from .env file
load_dotenv()

class ShoppingAgentSystem:
    """
    Encapsulated multi-agent system for handling shopping queries.
    This class initializes and manages a workflow of multiple agents,
    processes user queries, and streams the results back in real-time.
    """
    def __init__(self, config_path=None):
        """
        Initializes the agent system by loading configuration, setting up
        the language model, and defining the agents and workflow.
        """
        # --- ROBUST PATHING FIX ---
        # If no config path is provided, build an absolute path
        # from this file's location to the prompts.yaml file.
        if config_path is None:
            # Gets the directory where agent_system.py is located.
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Constructs the full, absolute path to the config file.
            # This assumes a structure like:
            # /your_project/
            #   - agent_system.py
            #   - src/
            #     - agents/
            #       - prompts.yaml
            config_path = os.path.join(base_dir, 'src', 'agents', 'prompts.yaml')

        print(f"Attempting to load configuration from: {config_path}")

        self.llm = create_gemini()
        self.config = self._load_config(config_path)
        self.agents = self._create_agents()
        self.workflow = self._create_workflow()
        self.current_agent_name = "UnknownAgent"
        print("✅ ShoppingAgentSystem initialized successfully.")

    def _load_config(self, file_path):
        """Loads agent configuration from a YAML file."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"❌ FATAL ERROR: Configuration file not found at {file_path}")
            print("Please ensure the path is correct and the file exists.")
            raise
        except Exception as e:
            print(f"❌ FATAL ERROR: Error loading or parsing config file: {e}")
            raise

    def _create_agents(self):
        """Creates all agents based on the loaded configuration."""
        agents = {}
        tools = [search_tool, visit_webpage, Get_info_from_url_tool]

        for agent_name, agent_config in self.config.items():
            agents[agent_name] = ReActAgent(
                name=agent_config["name"],
                description=agent_config.get("description", ""),
                system_prompt=agent_config.get("system_prompt", ""),
                tools=tools if agent_name != "manager_agent" else [],
                llm=self.llm,
                verbose=True
            )
        return agents

    def _create_workflow(self):
        """Creates the agent workflow with a specified root agent."""
        return AgentWorkflow(
            agents=list(self.agents.values()),
            root_agent="manager_agent",
        )

    def _get_agent_name_from_event(self, event):
        """Extracts the agent name from a workflow event."""
        if hasattr(event, 'source') and hasattr(event.source, 'name'):
            return event.source.name
        return self.current_agent_name

    async def run_workflow(self, user_prompt: str):
        """
        Runs the agent workflow for a given user prompt and yields
        formatted messages for each step in real-time.
        """
        ctx = Context(self.workflow)
        handler = self.workflow.stream_run(user_msg=user_prompt, ctx=ctx)

        async for event in handler.stream_events():
            agent_name = self._get_agent_name_from_event(event)
            if agent_name != "UnknownAgent":
                self.current_agent_name = agent_name

            if isinstance(event, ToolCallResult):
                tool_name = event.tool_name
                tool_input = event.tool_kwargs
                tool_output = str(event.tool_output)
                if len(tool_output) > 700:
                    tool_output = tool_output[:700] + "..."

                yield (
                    f"**🤖 Agent `{agent_name}` called Tool `{tool_name}`**\n"
                    f"**Input:** `{tool_input}`\n\n"
                    f"**Output:**\n---\n{tool_output}\n---"
                )

            elif isinstance(event, AgentStream):
                delta = getattr(event, "delta", "")
                if delta and delta.strip():
                    yield f"**🤔 Agent `{agent_name}` thinking:**\n{delta}"

        try:
            final_response = await handler
            # Access the .response attribute for the final string output
            yield f"**✅ Final Response:**\n\n{final_response.response}"
        except Exception as e:
            yield f"**❌ Error retrieving final response:** {str(e)}"