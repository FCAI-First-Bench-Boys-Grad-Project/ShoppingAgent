# libraries imports
import yaml
import asyncio
from datetime import datetime
from phoenix.otel import register
from llama_index.core.workflow import Context
from src.llms.gemini_2_flash import create_gemini
from llama_index.core.tools import QueryEngineTool
from llama_index.core.prompts import PromptTemplate
from llama_index.core.callbacks import CallbackManager
from llama_index.utils.workflow import draw_all_possible_flows
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from llama_index.core.agent.workflow import AgentWorkflow, ReActAgent, FunctionAgent
from llama_index.core.agent.workflow import AgentWorkflow, ToolCallResult, AgentStream

# Custom imports
from src.tools.web_search import search_tool
from src.tools.visit_webpage import visit_webpage_tool
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


def create_custom_react_prompt(agent_config):
    """Create a properly formatted ReAct prompt that maintains the required structure"""
    
    # Extract the core mission and instructions from your config
    core_instructions = agent_config["system_prompt"]
    
    # Create a ReAct-compatible prompt that integrates your instructions
    react_prompt = f"""You are a helpful AI assistant that can use tools to answer questions.

{core_instructions}

When responding, you must follow this exact format:

Thought: I need to think about what the user is asking and determine if I need to use any tools.
Action: [tool_name if using a tool, or skip this line if not using a tool]
Action Input: [tool input in JSON format if using a tool, or skip this line if not using a tool]
Observation: [This will be filled in by the tool response]

Continue this Thought/Action/Action Input/Observation cycle until you have enough information to provide a final answer.

When you have enough information, provide your final response in this format:

Thought: I now have enough information to provide a complete answer.
Answer: [Your final answer here]

Remember to always start with a Thought and follow the exact format above."""

    return react_prompt


async def main():
    # Create callback manager
    callback_manager = create_callback_manager()
    
    # phoenix handler
    # Register the tracer provider (connects to OpenTelemetry)
    tracer_provider = register()

    # Instrument LlamaIndex with OpenInference
    LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)

    # Create LLM with callback manager
    llm = create_gemini()
    if hasattr(llm, 'callback_manager'):
        llm.callback_manager = callback_manager

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

    # Create agents with proper prompt integration
    try:
        # Manager Agent
        manager_agent = ReActAgent(
            name=config["manager_agent"]["name"],
            description=config["manager_agent"]["description"],
            tools=[],
            llm=llm,
            callback_manager=callback_manager,
            verbose=True,  # Enable verbose mode for debugging
            can_handoff_to=["product_hunter_agent", "product_investigator_agent", "trivial_search_agent"],
        )
        
        # Create custom prompt template for manager
        manager_prompt = create_custom_react_prompt(config["manager_agent"])
        manager_agent.update_prompts({
            "react_header": PromptTemplate(manager_prompt)
        })

        # Product Hunter Agent
        product_hunter_agent = ReActAgent(
            name=config["product_hunter_agent"]["name"],
            description=config["product_hunter_agent"]["description"],
            tools=[search_tool, visit_webpage_tool, Get_info_from_url_tool],
            llm=llm,
            callback_manager=callback_manager,
            verbose=True,
            can_handoff_to=["manager_agent"],
            # can_be_handed_off_by=["manager_agent"]
        )
        
        hunter_prompt = create_custom_react_prompt(config["product_hunter_agent"])
        product_hunter_agent.update_prompts({
            "react_header": PromptTemplate(hunter_prompt)
        })

        # Trivial Search Agent
        trivial_search_agent = ReActAgent(
            name=config["trivial_search_agent"]["name"],
            description=config["trivial_search_agent"]["description"],
            tools=[search_tool, visit_webpage_tool, Get_info_from_url_tool],
            llm=llm,
            callback_manager=callback_manager,
            verbose=True,
            can_handoff_to=["manager_agent"],

        )
        
        trivial_prompt = create_custom_react_prompt(config["trivial_search_agent"])
        trivial_search_agent.update_prompts({
            "react_header": PromptTemplate(trivial_prompt)
        })

        # Product Investigator Agent
        product_investigator_agent = ReActAgent(
            name=config["product_investigator_agent"]["name"],
            description=config["product_investigator_agent"]["description"],
            tools=[search_tool, visit_webpage_tool, Get_info_from_url_tool],
            llm=llm,
            callback_manager=callback_manager,
            verbose=True,
            can_handoff_to=["manager_agent"],
        )
        
        investigator_prompt = create_custom_react_prompt(config["product_investigator_agent"])
        product_investigator_agent.update_prompts({
            "react_header": PromptTemplate(investigator_prompt)
        })

        print("✅ All agents created successfully!")

    except Exception as e:
        print(f"❌ Error creating agents: {e}")
        import traceback
        traceback.print_exc()
        return

    # Create workflow with callback manager
    try:
        workflow = AgentWorkflow(
            agents=[manager_agent, product_hunter_agent,
                    product_investigator_agent, trivial_search_agent],
            root_agent="manager_agent",
            # callback_manager=callback_manager,
            verbose=True,
        )
        print("✅ Workflow created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating workflow: {e}")
        import traceback
        traceback.print_exc()
        return

    # To keep memory
    ctx = Context(workflow)

    # Test prompts
    prompt = "I want to buy a wired headset for gaming for 500 USD or less."

    print(f"\n🎯 Starting Shopping Assistant Workflow")
    print(f"📝 Query: {prompt}")
    print(f"⏰ Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        handler = workflow.run(
            user_msg=prompt,
            ctx=ctx
        )

        # Create output file with timestamp
        output_filename = f"agent_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        # Agent name mapping for better identification
        agent_mapping = {
            agent.name: agent.name for agent in [
                manager_agent, product_hunter_agent, trivial_search_agent,
                product_investigator_agent, 
            ]
        }

        print(f"\n📄 Logging to: {output_filename}")

        with open(output_filename, "w", encoding="utf-8") as f:
            # Write session header
            session_header = f"""
Shopping Assistant Session Log
==============================
Session ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}
Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Query: {prompt}
Active Agents: {', '.join(agent_mapping.keys())}
==============================

"""
            f.write(session_header)
            print(session_header)

            current_agent = "Unknown"

            async for ev in handler.stream_events():
                timestamp = datetime.now().strftime("%H:%M:%S")
                agent_name = get_agent_name_enhanced(ev, workflow)

                # Update current agent tracking
                if agent_name != "UnknownAgent":
                    current_agent = agent_name
                else:
                    agent_name = current_agent

                if isinstance(ev, ToolCallResult):
                    tool_message = format_output_message(
                        agent_name,
                        "TOOL EXECUTION",
                        f"🛠 Tool: {ev.tool_name}\n"
                        f"📥 Input: {ev.tool_kwargs}\n"
                        f"📤 Output: {str(ev.tool_output)[:500]}{'...' if len(str(ev.tool_output)) > 500 else ''}",
                        timestamp
                    )
                    print(tool_message)
                    f.write(tool_message)

                elif isinstance(ev, AgentStream):
                    delta = getattr(ev, "delta", "")
                    if delta.strip():  # Only log non-empty deltas
                        stream_message = f"[{timestamp}] {agent_name} 💭: {delta}"
                        print(stream_message, end="", flush=True)
                        f.write(stream_message)

            # Write session footer
            session_footer = f"""

==============================
Session Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==============================
"""
            f.write(session_footer)
            print(session_footer)

        print("\n🎉 Workflow execution completed!")

        # Get final response
        try:
            resp = await handler
            final_response = format_output_message(
                "FINAL_RESPONSE",
                "WORKFLOW RESULT",
                str(resp)
            )
            print(final_response)

            # Append final response to file
            with open(output_filename, "a", encoding="utf-8") as f:
                f.write(final_response)

        except Exception as e:
            error_message = f"❌ Error getting final response: {str(e)}"
            print(error_message)
            with open(output_filename, "a", encoding="utf-8") as f:
                f.write(f"\n{error_message}\n")

    except Exception as e:
        print(f"❌ Error running workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())