"""FastAPI backend server for LogDoc SOC Triage Agent."""

import json
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.logdoc_agent import get_logdoc_agent

app = FastAPI(title="LogDoc API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TOOL_STATUS_MAP = {
    "search_playbooks_knowledge_base": "Searching knowledge base...",
    "search_web": "Searching the web...",
}

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
print(f"Loading .env file from {ROOT_DIR / '.env'}")
load_dotenv(ROOT_DIR / ".env", override=True)


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Stream chat responses from the LogDoc agent via Server-Sent Events."""
    agent = get_logdoc_agent()
    graph = agent.graph

    print(f"Agent model: {agent.llm.model_name}")

    lc_messages = []
    for msg in request.messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))

    # Run IDs for runs that are inside a tool (e.g. RAG retriever's LLM). We skip streaming their tokens.
    tool_descendant_run_ids = set()

    async def generate():
        try:
            async for event in graph.astream_events(
                {"messages": lc_messages},
                config={"recursion_limit": 10},
                version="v2",
            ):
                kind = event["event"]
                run_id = event.get("run_id")
                parent_ids = event.get("parent_ids") or []

                # Mark this run and all descendants of tool runs so we don't stream their LLM output
                if any(pid in tool_descendant_run_ids for pid in parent_ids):
                    tool_descendant_run_ids.add(run_id)

                if kind == "on_tool_start":
                    tool_descendant_run_ids.add(run_id)
                    tool_name = event.get("name", "")
                    status = TOOL_STATUS_MAP.get(tool_name, f"Using {tool_name}...")
                    yield f"data: {json.dumps({'type': 'status', 'content': status})}\n\n"

                elif kind == "on_tool_end":
                    yield f"data: {json.dumps({'type': 'status', 'content': ''})}\n\n"

                elif kind == "on_chat_model_stream":
                    # Only stream tokens from the main agent's LLM, not from tool-internal LLMs (e.g. RAG)
                    if run_id in tool_descendant_run_ids:
                        continue
                    chunk = event["data"]["chunk"]
                    content = chunk.content
                    if isinstance(content, str) and content:
                        yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                                yield f"data: {json.dumps({'type': 'token', 'content': item['text']})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
