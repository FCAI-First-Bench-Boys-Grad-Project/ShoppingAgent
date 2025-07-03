import uuid
import streamlit as st
from ShoppingAgent import ShoppingAgent
from dotenv import load_dotenv


# --- Constants and Configuration ---
RECURSION_LIMIT = 100

# --- Environment and API Setup ---
load_dotenv()
# Ensure you have LANGCHAIN_API_KEY, etc., in your .env file
# client = Client() # You can uncomment this if you use it explicitly elsewhere

# --- Helper Functions ---


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


def render_shopping_list():
    """Renders the interactive shopping list in the sidebar."""
    st.header("🛒 Shopping List")

    shopping_list = st.session_state.shopping_list

    if not shopping_list:
        st.info("Your shopping list is empty. Add items from the chat!")
    else:
        # Using a list of dicts: [{'name': 'Product A', 'url': '...'}, ...]
        for i, item in enumerate(shopping_list):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{item['name']}**")
                    # Shorten URL for display but keep the full link
                    display_url = item['url'].split('//')[-1].split('/')[0]
                    st.markdown(f"[{display_url}]({item['url']})")
                with col2:
                    # Use the item's index for the key to ensure uniqueness
                    if st.button("🗑️", key=f"remove_{i}", help="Remove item"):
                        st.session_state.shopping_list.pop(i)
                        st.rerun()

        # Add a button to clear the entire list
        st.divider()
        if st.button("Clear All Items", use_container_width=True):
            st.session_state.shopping_list = []
            st.rerun()


# --- Main Application UI ---

# Call initialization function at the start
initialize_state()

# --- Page Configuration ---
st.set_page_config(
    page_title="🤖 Shopping Agent Pro",
    page_icon="🛒",
    layout="wide"
)

# --- Sidebar UI ---
with st.sidebar:
    st.title("🛍️ Your Assistant")
    st.caption("Manage your list and see the agent's thoughts.")

    # This placeholder will be updated with the agent's thought process
    agent_thoughts_placeholder = st.container()

    render_shopping_list()


# --- Main Chat Interface ---
st.title("🤖🛒 Shopping Agent Pro")
st.caption("I can search the web, compare products, and build your shopping list.")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle chat input and agent interaction
if prompt := st.chat_input("e.g., Find me the best noise-cancelling headphones under $300"):
    # Add user message to UI and history
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare for agent's response
    with st.chat_message("assistant"):
        final_response_container = st.empty()

        # Use st.status for a cleaner "thinking" process display
        with agent_thoughts_placeholder.status("🕵️ Agent is thinking...", expanded=True) as status:
            full_response_content = ""

            # The stream generator for the final response
            def stream_generator():
                last_chunk = None
                for chunk in st.session_state.agent.ShoppingAgent.stream(
                    {"messages": [{"role": "user", "content": prompt}]},
                    config={"recursion_limit": RECURSION_LIMIT, "configurable": {
                        "thread_id": st.session_state.thread_id}},
                    stream_mode="updates"
                ):
                    last_chunk = chunk

                    # --- Update Agent Thoughts in Sidebar ---
                    if thoughts := next(iter(chunk.values()), {}).get('thoughts'):
                        # Format thoughts for better readability
                        formatted_thoughts = "\n\n---\n\n".join(thoughts)
                        status.markdown(
                            f"```markdown\n{formatted_thoughts}\n```")

                    # --- Yield Final Response for Streaming in Main Chat ---
                    if final_answer_chunk := next(iter(chunk.values()), {}).get('final_response'):
                        yield final_answer_chunk
                    elif messages_chunk := next(iter(chunk.values()), {}).get('messages'):
                        # LangGraph often streams the final message content this way
                        yield messages_chunk[-1].content

                # After the loop, process the final state from the last chunk
                final_state = next(iter(last_chunk.values()), {})

                # Update shopping list in session state
                # Assuming the agent returns a list of dicts: [{'name': '...', 'url': '...'}]
                products_raw = final_state.get('products', [])
                # Handle flat list [name, url, name, url]
                if products_raw and isinstance(products_raw[0], str):
                    updated_products = [
                        {'name': products_raw[i], 'url': products_raw[i+1]} for i in range(0, len(products_raw), 2)]
                else:  # Assumes list of dicts
                    updated_products = products_raw

                st.session_state.shopping_list.extend(updated_products)

            # Stream the final response to the main chat window
            full_response = final_response_container.write_stream(
                stream_generator)

        # Update status box to "complete"
        status.update(label="Agent finished!",
                      state="complete", expanded=False)

        # Add final agent response to the message history
        if full_response:
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response})

        # Rerun to update the shopping list displayed in the sidebar
        st.rerun()
