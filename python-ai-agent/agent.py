import os
import json
import urllib.parse
from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import httpx

# MCP Client
from mcp import ClientSession
from mcp.client.sse import sse_client

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:4000/sse")

# Global variables for the MCP session
mcp_session = None
exit_stack = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_session, exit_stack
    exit_stack = AsyncExitStack()
    print(f"[Agent] Connecting to MCP Server at {MCP_SERVER_URL}...")
    try:
        sse_transport = await exit_stack.enter_async_context(sse_client(MCP_SERVER_URL))
        mcp_session = await exit_stack.enter_async_context(ClientSession(sse_transport[0], sse_transport[1]))
        await mcp_session.initialize()
        print("[Agent] Successfully connected to MCP Server via SSE")
    except Exception as e:
        print(f"[Agent] Failed to connect to MCP Server: {e}")
    yield
    await exit_stack.aclose()

app = FastAPI(lifespan=lifespan)

# --- Define LangChain Tools that proxy to our MCP server ---

@tool
async def detect_audience(text: str) -> str:
    """Detect the appropriate audience for a given technical text. Returns a string representing the audience (management, marketing, engineering, general)."""
    print(f"[Tool Executing] detect_audience")
    result = await mcp_session.call_tool("detect_audience", arguments={"text": text})
    return result.content[0].text

@tool
async def simplify_text(text: str, audience: str) -> str:
    """Simplify technical text based on specific audience requirements."""
    print(f"[Tool Executing] simplify_text")
    result = await mcp_session.call_tool("simplify_text", arguments={"text": text, "audience": audience})
    return result.content[0].text

@tool
async def validate_accuracy(original_text: str, simplified_text: str) -> dict:
    """Validate if simplified text maintains key technical meaning compared to original."""
    print(f"[Tool Executing] validate_accuracy")
    result = await mcp_session.call_tool("validate_accuracy", arguments={
        "original_text": original_text,
        "simplified_text": simplified_text
    })
    return json.loads(result.content[0].text)

tools = [detect_audience, simplify_text, validate_accuracy]

# Build the LangGraph ReAct Agent
llm = ChatOpenAI(
    model="google/gemini-2.5-pro",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.2
)

agent = create_react_agent(llm, tools)

async def process_and_respond(text: str, response_url: str):
    print(f"[Agent] Starting autonomous ReAct reasoning loop for text: {text[:30]}...")
    try:
        system_prompt = (
            "You are an autonomous AI Agent responsible for converting technical text into business communication. "
            "You MUST use the provided tools to detect audience, simplify the text, and then validate it. "
            "If validation fails, retry the simplification with stricter facts AT MOST ONCE. "
            "If it fails validation a second time, immediately return the best simplified text you have without looping further. "
            "Once valid (or after 1 retry), return the final simplified text."
        )
        
        # Invoke the ReAct graph
        result = await agent.ainvoke({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please simplify this text: {text}"}
            ]
        })
        
        final_message = result["messages"][-1].content
        print("[Agent] Finished processing. Sending response to Slack.")
        
        # Send response back to Slack
        async with httpx.AsyncClient() as client:
            await client.post(response_url, json={
                "response_type": "in_channel",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Simplified Text:*\n{final_message}"
                        }
                    }
                ]
            })
            
    except Exception as e:
        print(f"Error processing async task: {e}")
        async with httpx.AsyncClient() as client:
            await client.post(response_url, json={
                "text": "An error occurred while processing your request."
            })

@app.post("/slack/simplify")
async def slack_endpoint(req: Request, background_tasks: BackgroundTasks):
    body_bytes = await req.body()
    body_str = body_bytes.decode('utf-8')
    parsed = urllib.parse.parse_qs(body_str)
    
    text = parsed.get("text", [""])[0]
    response_url = parsed.get("response_url", [""])[0]
    
    if not text:
        return JSONResponse({"response_type": "ephemeral", "text": "Please provide text to simplify."})

    # Kick off background task
    background_tasks.add_task(process_and_respond, text, response_url)
    
    # Return immediate 200 OK so Slack doesn't timeout and retry!
    return JSONResponse({
        "response_type": "ephemeral", 
        "text": "Agent is reasoning and processing your request... 🧠"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
