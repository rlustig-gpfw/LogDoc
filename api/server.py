"""FastAPI backend server for LogDoc SOC Triage Agent."""

import json
from pathlib import Path
import sys
import os
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from src.agent.logdoc_agent import LogDocState, get_logdoc_agent

ROOT_DIR = Path(__file__).resolve().parents[1]
print(f"Loading .env file from {ROOT_DIR / '.env'}")
load_dotenv(ROOT_DIR / ".env", override=True)

app = FastAPI(title="LogDoc API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ConversationMessage(BaseModel):
    role: str
    content: str


class AnalyzeRequest(BaseModel):
    """Request to analyze (or re-analyze) logs for a case.

    The frontend sends current case context and any existing structured results.
    Conversation history is optional (used to re-run after chat).
    """
    user_query: str
    active_case_id: Optional[str] = None
    active_case_title: Optional[str] = None
    selected_log_data: Optional[Dict[str, Any]] = None
    triage_result: Optional[Dict[str, Any]] = None
    playbook_result: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[ConversationMessage]] = None


class ChatRequest(BaseModel):
    """Follow-up chat request tied to an active case.

    The frontend sends the current structured case state so the agent can
    answer without re-running triage or playbook unless the router decides it
    is needed.
    """
    user_query: str
    active_case_id: Optional[str] = None
    active_case_title: Optional[str] = None
    selected_log_data: Optional[Dict[str, Any]] = None
    triage_result: Optional[Dict[str, Any]] = None
    playbook_result: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[ConversationMessage]] = None


# ---------------------------------------------------------------------------
# Node names that emit status messages to the UI
# ---------------------------------------------------------------------------

NODE_STATUS_MAP = {
    "context_resolver": "Resolving context...",
    "router": "Planning route...",
    "log_triage": "Analyzing logs...",
    "playbook_retrieval": "Searching playbooks...",
    "response_composer": "Composing response...",
}

TOOL_STATUS_MAP = {
    "search_playbooks_knowledge_base": "Searching knowledge base...",
    "search_web": "Searching the web...",
}


# ---------------------------------------------------------------------------
# Shared stream helper
# ---------------------------------------------------------------------------

def _build_state(
    user_query: str,
    active_case_id: Optional[str],
    active_case_title: Optional[str],
    selected_log_data: Optional[Dict[str, Any]],
    triage_result: Optional[Dict[str, Any]],
    playbook_result: Optional[Dict[str, Any]],
    conversation_history: Optional[List[ConversationMessage]],
) -> LogDocState:
    history = (
        [{"role": m.role, "content": m.content} for m in conversation_history]
        if conversation_history
        else []
    )
    return LogDocState(
        user_query=user_query,
        active_case_id=active_case_id,
        active_case_title=active_case_title,
        selected_log_data=selected_log_data,
        triage_result=triage_result,
        playbook_result=playbook_result,
        conversation_history=history,
    )


async def _stream_graph(initial_state: LogDocState):
    """Async generator that streams graph events as SSE data lines.

    Yields:
      - status events for node start / tool use
      - token events for response_composer LLM output
      - result event (JSON) with final triage_result, playbook_result, intent, route_plan
      - done event
    """
    agent = get_logdoc_agent()
    graph = agent.graph

    # Track run ids for response_composer so we only stream its tokens
    composer_run_ids: set = set()
    tool_run_ids: set = set()

    try:
        async for event in graph.astream_events(
            initial_state,
            config={"recursion_limit": 10},
            version="v2",
        ):
            kind = event["event"]
            run_id = event.get("run_id")
            parent_ids = event.get("parent_ids") or []
            metadata = event.get("metadata") or {}
            node_name = metadata.get("langgraph_node") or event.get("name") or ""

            # Propagate composer run ids to children
            if node_name == "response_composer":
                composer_run_ids.add(run_id)
            if any(pid in composer_run_ids for pid in parent_ids):
                composer_run_ids.add(run_id)

            # Track tool runs (we suppress their internal LLM tokens)
            if kind == "on_tool_start":
                tool_run_ids.add(run_id)
                tool_name = event.get("name", "")
                status = TOOL_STATUS_MAP.get(tool_name, f"Using {tool_name}...")
                yield f"data: {json.dumps({'type': 'status', 'content': status})}\n\n"
                continue

            if any(pid in tool_run_ids for pid in parent_ids):
                tool_run_ids.add(run_id)

            if kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'status', 'content': ''})}\n\n"
                continue

            if kind == "on_chain_start":
                name = event.get("name", "")
                if name in NODE_STATUS_MAP:
                    yield f"data: {json.dumps({'type': 'status', 'content': NODE_STATUS_MAP[name]})}\n\n"
                continue

            if kind == "on_chain_end" and event.get("name") == "LangGraph":
                # The compiled graph emits on_chain_end with name "LangGraph" when it finishes.
                # This is where the complete final state (including structured outputs) is available.
                data = event.get("data") or {}
                output = data.get("output") or {}
                result_payload = {
                    "type": "result",
                    "final_response": output.get("final_response") or "",
                    "triage_result": output.get("triage_result"),
                    "playbook_result": output.get("playbook_result"),
                    "intent": output.get("intent"),
                    "route_plan": output.get("route_plan"),
                }
                yield f"data: {json.dumps(result_payload)}\n\n"
                continue

            if kind == "on_chat_model_stream":
                # Skip tokens from tool-internal LLMs
                if run_id in tool_run_ids:
                    continue
                # Only stream from response_composer
                if run_id not in composer_run_ids and not any(pid in composer_run_ids for pid in parent_ids):
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze_endpoint(request: AnalyzeRequest):
    """Stream a full case analysis.

    The frontend sends the selected case + optional existing structured results.
    The graph runs context_resolver → router → [log_triage] → [playbook_retrieval] → response_composer.
    Streamed events: status, token (response_composer output), result (structured JSON), done.
    """
    state = _build_state(
        user_query=request.user_query,
        active_case_id=request.active_case_id,
        active_case_title=request.active_case_title,
        selected_log_data=request.selected_log_data,
        triage_result=request.triage_result,
        playbook_result=request.playbook_result,
        conversation_history=request.conversation_history,
    )
    return StreamingResponse(
        _stream_graph(state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Stream a follow-up chat response for an active case.

    The frontend sends the current case state (structured triage + playbook results) and
    the conversation history. The router decides whether to use existing results or run
    new specialist nodes.
    Streamed events: status, token (response_composer output), result (structured JSON), done.
    """
    state = _build_state(
        user_query=request.user_query,
        active_case_id=request.active_case_id,
        active_case_title=request.active_case_title,
        selected_log_data=request.selected_log_data,
        triage_result=request.triage_result,
        playbook_result=request.playbook_result,
        conversation_history=request.conversation_history,
    )
    return StreamingResponse(
        _stream_graph(state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
