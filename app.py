import os
import json
import chainlit as cl
import asyncio
from dotenv import load_dotenv
from data_layer import InMemoryDataLayer
from flow import create_agent_flow

#@cl.data_layer
#def get_data_layer():
#    return InMemoryDataLayer()

@cl.on_chat_start
async def start():
    """
    This function runs when a new user session begins.
    """
    load_dotenv()
    # Send a welcome message
    await cl.Message(
        content="👋 Hello! I am your Deep Research Agent.\n\nI can break down complex topics into detailed reports. What would you like me to research today?"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """
    When the user sends a message, we run the research workflow 
    and return the final report.
    """
    
    user_query = message.content

    # Initial shared state for PocketFlow
    shared = {
        "user_query": user_query,
        "goal": None,
        "constraints": {},
        "plan": {},
        "notes": {},
        "reflection": {},
        "report": "",
        "steps": 0,
    }

    # Create the research flow
    flow = create_agent_flow()

    # Optional: send a "progress" message
    progress = await cl.Message(content="🔍 Starting deep research...").send()
    await flow.run_async(shared)
    progress.content="✅ Research complete!"
    await progress.update()

    # Send final report
    await cl.Message(content=shared.get("report", "No answer found")).send()
