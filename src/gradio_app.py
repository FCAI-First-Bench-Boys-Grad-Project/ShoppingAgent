# gradio_app.py

import gradio as gr
import traceback
from agent_system import ShoppingAgentSystem

# --- IMPROVED INITIALIZATION AND ERROR LOGGING ---
try:
    # This will now use the robust pathing from agent_system.py
    agent_system = ShoppingAgentSystem()
    SYSTEM_READY = True
except Exception as e:
    # This will print the full error to your console for easy debugging
    print("---" * 20)
    print("🚨 FATAL: Failed to initialize ShoppingAgentSystem. The app will not work.")
    print(f"Error: {e}")
    print("Full Traceback:")
    traceback.print_exc()
    print("---" * 20)
    agent_system = None
    SYSTEM_READY = False

async def chat_interface(message: str, history: list):
    """
    The main function that powers the Gradio chat interface.
    It handles updating both the chatbot and clearing the input box.
    """
    if not SYSTEM_READY:
        history.append([message, "The agent system is not available. Please check the console for errors."])
        yield history, gr.update(value="")
        return

    history.append([message, ""])
    yield history, gr.update(value="") # Update UI to show user message and clear input

    full_response = ""
    async for chunk in agent_system.run_workflow(message):
        full_response += chunk + "\n\n"
        history[-1][1] = full_response
        yield history, gr.update() # Update chatbot with streaming response

def build_gradio_app():
    """Builds and returns the Gradio web application interface."""
    with gr.Blocks(theme=gr.themes.Soft(), title="Multi-Agent Shopping Assistant") as app:
        gr.Markdown(
            """
            # 🛍️ Multi-Agent Shopping Assistant
            Ask me to find products, compare prices, or research items for you.
            I will show you the step-by-step actions taken by my team of agents.
            """
        )

        chatbot = gr.Chatbot(
            label="Conversation",
            bubble_full_width=False,
            height=600,
            avatar_images=(
                "https://img.icons8.com/fluency/48/user-male-circle--v1.png",
                "https://img.icons8.com/arcade/64/robot-2.png"
            )
        )

        with gr.Row():
            msg_textbox = gr.Textbox(
                placeholder="e.g., 'Find me the best gaming laptop under $1500'",
                scale=4,
                container=False,
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)

        outputs = [chatbot, msg_textbox]

        msg_textbox.submit(chat_interface, [msg_textbox, chatbot], outputs, queue=True)
        submit_btn.click(chat_interface, [msg_textbox, chatbot], outputs, queue=True)

        gr.Examples(
            examples=[
                "I want a good wired headset for gaming in range of 1000EGP.",
                "I want to build a Gaming PC for around 50k EGP with great performance for 1080p gaming.",
                "I want to buy a wedding suit with a tie for a maximum budget of 30k EGP in Cairo.",
            ],
            inputs=[msg_textbox],
            label="Example Prompts"
        )
    return app

if __name__ == "__main__":
    web_app = build_gradio_app()
    web_app.launch(debug=True, share=True)