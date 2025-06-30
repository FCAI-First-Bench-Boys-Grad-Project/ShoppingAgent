# app.py

import streamlit as st
from shopping_agent import ShoppingAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="🤖 Shopping Agent",
    page_icon="🛒",
    layout="wide"
)

# --- State Management ---
if "agent" not in st.session_state:
    st.session_state.agent = ShoppingAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add initial assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": "Hello! How can I help you with your shopping today?"}
    )

# --- UI Rendering ---
st.title("🤖🛒 Your Personal Shopping Agent")
st.caption("I can search the web, analyze products, and help you build your shopping list.")

# Sidebar for Shopping List and Agent Internals
with st.sidebar:
    st.header("🛒 Shopping List")
    # Use the definitive state from the agent instance
    shopping_list = st.session_state.agent.state.get("shopping_list", [])
    if not shopping_list:
        st.info("Your shopping list is empty.")
    else:
        for i, item in enumerate(shopping_list):
            st.markdown(f"**{i+1}. {item.get('name', 'N/A')}**")
            if url := item.get('url'):
                st.markdown(f"   - **URL:** [{url.split('//')[-1]}]({url})")
            st.markdown(f"   - **Details:** {item.get('details', 'No details provided.')}")
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

        with st.spinner("Processing..."):
            # The run_agent method is a generator that yields thought strings
            for thought in st.session_state.agent.run_agent(prompt):
                thought_log.append(thought)
                # Update the placeholder with the growing log of thoughts
                agent_thoughts_placeholder.markdown("\n\n---\n\n".join(thought_log))

            # After the generator is exhausted, the agent's state is fully updated
            # Get the final response from the last message in the agent's state
            final_response = st.session_state.agent.state["messages"][-1].content
            response_placeholder.markdown(final_response)

    # Add final agent response to the UI history
    st.session_state.messages.append({"role": "assistant", "content": final_response})
    
    # Rerun the script to update the sidebar with the new shopping list
    st.rerun()