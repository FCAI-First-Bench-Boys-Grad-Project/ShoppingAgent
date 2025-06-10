# --- In your gradio_app.py ---
# import gradio as gr
from UIAgentSystem import UIAgentSystem

# 1. Create a single, persistent instance of your agent system
agent_system = UIAgentSystem()

# 2. Define the function that Gradio will call
def chat_interface_fn(user_message, history):
    history = history or []
    
    # This is the key part:
    # We loop through the generator provided by our agent system
    # Each `update` is a dictionary we defined in our CallbackHandler
    for update in agent_system.stream_agent_responses(user_message):
        
        # Now, you process the update dictionary
        if update['type'] == 'thought':
            # This is a thought from the agent. Maybe display it in a special "status" box.
            status_update = f"Thinking: {update['content']}"
            # You would update some gr.Textbox or gr.Markdown component here.
            print(status_update) # For console testing

        elif update['type'] == 'tool_end':
            # A tool finished. Display which tool was used and its result.
            status_update = f"✅ Used Tool: `{update['tool_name']}` -> Got result: `{update['tool_output']}`"
            # Update the status box again.
            print(status_update)

        elif update['type'] == 'final_answer':
            # This is the final answer. Append it to the chat history.
            final_message = update['content']
            history.append((user_message, final_message))
            # yield the updated history to the Gradio Chatbot
            # yield history
            print(f"Final Answer: {final_message}")

    # Return the final state after the loop is done.
    # return history

# 3. Launch your Gradio interface
# chatbot = gr.Chatbot()
# with gr.Blocks() as demo:
#     ... your UI layout ...
#     textbox.submit(chat_interface_fn, [textbox, chatbot], [chatbot])
# demo.launch()