import uuid
import gradio as gr

# Import our custom modules
from database import build_db_if_needed
from agent import create_agent

# ─── Startup Tasks ──────────────────────────────────────────────────────────
# 1. Ensure the database is built before launching the app
try:
    build_db_if_needed()
except Exception as e:
    print(f"\n[STARTUP ERROR] Failed to initialize database: {e}")
    # We won't crash immediately so the UI can still load, 
    # but the agent will likely fail if the DB isn't there.

# ─── Gradio Chat Logic ──────────────────────────────────────────────────────
def chat(message: str, history: list, session_state: dict):
    """Gradio chat handler. Maintains one Agno agent per browser session."""
    if "agent" not in session_state:
        session_state["user_id"]   = f"user_{str(uuid.uuid4())[:8]}"
        session_state["session_id"] = str(uuid.uuid4())
        # DB_PATH is handled inside agent.py now!
        session_state["agent"]     = create_agent(
            session_state["session_id"],
            session_state["user_id"],
        )

    agent = session_state["agent"]
    uid   = session_state["user_id"]

    try:
        response = agent.run(message, user_id=uid)
        return response.content
    except Exception as e:
        return f"⚠️ Agent error: {e}"

# ─── Gradio UI Definition ───────────────────────────────────────────────────
with gr.Blocks(title="Greater Noida Real Estate Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🏠 Greater Noida Real Estate Agent
        Ask me anything about rentals in Greater Noida.
        - *"Show me 2 BHK flats in Chi 5 under ₹25,000"*
        - *"Is ₹31,000 for 1114 sqft in Chi V a good deal?"*
        - *"Find hospitals near Nimbus Express Park View 2"*
        """
    )

    session_state = gr.State({})

    chatbot = gr.ChatInterface(
        fn=lambda msg, hist: chat(msg, hist, session_state.value),
        chatbot=gr.Chatbot(height=500, render_markdown=True, type="messages"),
        textbox=gr.Textbox(placeholder="Ask about properties, deals, or amenities…", scale=7),
        submit_btn="Send",
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True)