import gradio as gr
from agent import create_agent

# Use global variables to ensure the Agent and the Tools connection are never deleted by the garbage collector
real_estate_agent = None
mcp_connection = None 

async def get_agent():
    global real_estate_agent, mcp_connection
    if real_estate_agent is None:
        print("Connecting to MCP Server via SSE...")
        # We capture the mcp_tools object so it doesn't get garbage collected
        real_estate_agent, mcp_connection = await create_agent(session_id="gradio_1", user_id="user_1")
        print("Connected successfully!")
    return real_estate_agent

async def chat_with_agent(message, history):
    try:
        agent = await get_agent()
        
        # We use await agent.arun() because the MCP SSE tools run asynchronously over the web port
        response = await agent.arun(message)
        
        return response.content
    except Exception as e:
        return f"🚨 **Error connecting to tools:** {e}\n\n*Did you remember to leave `python mcp_server.py` running in a separate terminal? And did you fix your AZURE_DEPLOYMENT in the .env file?*"

# Build the Gradio Chat Interface
demo = gr.ChatInterface(
    fn=chat_with_agent,
    type="messages", # This clears the Gradio deprecation warning
    title="Greater Noida Real Estate AI Agent 🏠",
    description="I can help you find housing, evaluate deals, and locate amenities. What are you looking for today?"
)

if __name__ == "__main__":
    demo.launch()