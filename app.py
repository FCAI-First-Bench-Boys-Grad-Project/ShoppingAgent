import uuid
import streamlit as st
from ShoppingAgent import ShoppingAgent
from dotenv import load_dotenv
from langsmith import Client
import os

client = Client()
RECURSION_LIMIT = 100
# Load environment variables
load_dotenv()


def initialize_state():
    """Initializes all the necessary session state variables."""
    if "agent" not in st.session_state:
        # Initialize the agent once and store it in session state
        st.session_state.agent = ShoppingAgent()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add the initial welcome message
        st.session_state.messages.append(
            {"role": "assistant",
                "content": "Hello! How can I help you find the perfect products today?"}
        )

    # We will now use a list of dictionaries for the shopping list for easier management
    if "shopping_list" not in st.session_state:
        st.session_state.shopping_list = []

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())


initialize_state()
# --- Page Configuration ---
st.set_page_config(
    page_title="🤖 Shopping Agent",
    page_icon="🛒",
    layout="wide"
)

# --- UI Rendering ---
st.title("🤖🛒 Your Personal Shopping Agent")
st.caption(
    "I can search the web, analyze products, and help you build your shopping list.")

# Sidebar for Shopping List and Agent Internals
with st.sidebar:
    st.header("🛒 Shopping List")
    # Use the definitive state from the agent instance
    shopping_list = st.session_state.shopping_list
    if not shopping_list:
        st.info("Your shopping list is empty.")
    else:
        # shopping_list is a flat list: [name1, url1, name2, url2, ...]
        for i in range(0, len(shopping_list), 2):
            item_name = shopping_list[i]
            url = shopping_list[i + 1] if i + 1 < len(shopping_list) else ""
            st.markdown(f"**{(i//2)+1}. {item_name}**")
            st.markdown(f"   - **URL:** [{url.split('//')[-1]}]({url})")
            st.divider()

    st.header("🕵️ Agent Thoughts")
    # This placeholder will be updated as the agent runs
    agent_thoughts_placeholder = st.container(height=350, border=True)

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input and Agent Interaction ---
if prompt := st.chat_input("e.g., Find me the best budget wireless earbuds"):
    # Add user message to UI and history
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display agent's response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        thought_log = []
        last_chunk = None
        with st.spinner("Processing..."):
            # response = st.session_state.agent.ShoppingAgent(prompt)
            # final_response = response['final_response']
            # st.session_state.shopping_list = response['products']
            # The run_agent method is a generator that yields thought strings
            for chunk in st.session_state.agent.ShoppingAgent.stream(
                {"messages": [
                    {"role": "user", "content": prompt}]
                 },
                config={
                    "recursion_limit": RECURSION_LIMIT,
                    "configurable": {"thread_id": st.session_state.thread_id}
                },
                stream_mode="updates"
            ):
                last_chunk = chunk
                thought_log = next(iter(chunk.values())).get('thoughts', "")
                if thought_log == "":
                    continue
                # Update the placeholder with the growing log of thoughts
                agent_thoughts_placeholder.markdown(
                    "\n\n---\n\n".join(thought_log))
                # print(chunk)
                # print("\n")
                # st.rerun()

            # After the generator is exhausted, the agent's state is fully updated
            # Get the final response from the last message in the agent's state
            # final_response = st.session_state.agent.state["final_response"]
    final_response = next(iter(chunk.values())).get('final_response', "")
    if final_response == "":
        final_response = next(iter(chunk.values())).get(
            'messages', "")[-1].content
    response_placeholder.markdown(final_response)
    st.session_state.shopping_list = next(
        iter(chunk.values())).get('products', [])
    # Add final agent response to the UI history
    st.session_state.messages.append(
        {"role": "assistant", "content": final_response})

    # Rerun the script to update the sidebar with the new shopping list
    st.rerun()
