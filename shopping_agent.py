# shopping_agent.py

from src.tools import search_tool, query_url_tool, run_code_tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage, BaseMessage, AIMessage
from typing import Literal, List, Dict, Any, TypedDict, Annotated, Generator
from langchain_core.tools import tool
import operator
import yaml

# --- State Definition ---
class ShoppingState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    shopping_list: List[Dict[str, Any]]

# --- Custom Tools ---
@tool
def add_to_list_tool(name: str, url: str, details: str) -> str:
    """
    Adds a specified item to the user's shopping list.

    Args:
        name: The name of the product.
        url: The URL of the product page.
        details: Any important details about the product (e.g., price, color, size).
    """
    # This tool's primary purpose is to signal the intent to add to the list.
    # The _tool_node will handle the actual state modification.
    return f"✅ Item '{name}' is ready to be added to your shopping list."

# --- ShoppingAgent Class ---
class ShoppingAgent:
    def __init__(self, model: str = "qwen/qwen3-235b-a22b"):
        self.llm = ChatNVIDIA(model=model, max_tokens=8192)
        
        self.environment_tools = [search_tool, query_url_tool, run_code_tool]
        self.state_tools = [add_to_list_tool]
        self.tools = self.environment_tools + self.state_tools
        self.tools_by_name = {t.name: t for t in self.tools}
        
        self.llm_with_tools = self.llm.bind_tools(self.tools, parallel_tool_calls=True)
        self.agent = self._build_agent()
        self.state: ShoppingState = {"messages": [], "shopping_list": []}

    def _build_agent(self) -> StateGraph:
        builder = StateGraph(ShoppingState)
        builder.add_node("llm_call", self._llm_call)
        builder.add_node("tool_node", self._tool_node)
        builder.add_edge(START, "llm_call")
        builder.add_conditional_edges(
            "llm_call", self._should_continue,
            {"Action": "tool_node", END: END}
        )
        builder.add_edge("tool_node", "llm_call")
        return builder.compile()

    def _load_system_prompt(self) -> SystemMessage:
        try:
            with open("src\prompts.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            prompt = config.get("ShoppingAgent", {}).get("system_prompt", "You are a helpful assistant.")
        except Exception as e:
            print(e)
            prompt = "You are a helpful shopping assistant. Be friendly and efficient."
        return SystemMessage(content=prompt)

    def _llm_call(self, state: ShoppingState) -> Dict[str, List[BaseMessage]]:
        system_msg = self._load_system_prompt()
        print("This is the system : ",system_msg)
        messages = [system_msg] + state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def _should_continue(self, state: ShoppingState) -> Literal["Action", END]:
        last_msg = state["messages"][-1]
        return "Action" if hasattr(last_msg, "tool_calls") and last_msg.tool_calls else END

    def _tool_node(self, state: ShoppingState) -> Dict[str, Any]:
        """
        This node executes tools and returns updates to the state.
        It is now a "pure function" that doesn't modify self.state directly.
        """
        tool_results = []
        # The shopping list from the current state in the graph
        updated_shopping_list = state.get("shopping_list", []).copy()

        last_msg = state["messages"][-1]
        if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
            return {}

        for call in last_msg.tool_calls:
            tool_func = self.tools_by_name.get(call["name"])
            if not tool_func:
                obs = f"⚠️ Error: Tool '{call['name']}' not found."
            else:
                try:
                    # Special handling for our state-modifying tool
                    if call["name"] == "add_to_list_tool":
                        updated_shopping_list.append(call["args"])
                        obs = f"✅ Added '{call['args'].get('name')}' to your shopping list."
                    else:
                        obs = tool_func.invoke(call["args"])
                except Exception as e:
                    obs = f"⚠️ Error running {call['name']}: {e}"
            
            tool_results.append(ToolMessage(content=str(obs), tool_call_id=call["id"]))

        return {
            "messages": tool_results,
            "shopping_list": updated_shopping_list, # Return the new list
        }

    def run_agent(self, user_input: str) -> Generator[str, None, None]:
        """
        Runs the agent graph and yields 'thought' updates for the Streamlit UI.
        Manages state synchronization after the run is complete.
        """
        self.state["messages"].append(HumanMessage(content=user_input))
        
        graph_stream = self.agent.stream(self.state, stream_mode="values")
        final_state = None

        for step_output in graph_stream:
            final_state = step_output # Keep track of the latest state
            
            if "llm_call" in step_output:
                yield "🧠 **Planning:** Deciding next steps..."
                
            elif "tool_node" in step_output:
                for tool_call in step_output["llm_call"]["messages"][-1].tool_calls:
                    yield f"🛠️ **Tool Call:** `{tool_call['name']}`\n" \
                          f"   - **Arguments:** `{tool_call['args']}`"
                
                # Yield the results from the tool messages
                for tool_message in step_output['tool_node']['messages']:
                     yield f"✔️ **Tool Result:**\n   - `{tool_message.content}`"

        # After the stream is complete, update the agent's main state
        if final_state:
            self.state = final_state