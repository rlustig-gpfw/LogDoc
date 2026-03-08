"""
LogDoc SOC investigation graph

Graph:
    context_resolver → router → [log_triage] → [playbook_retrieval] → response_composer
"""

import json
import re
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from src.agent.tools import get_current_date, search_playbooks_knowledge_base, search_web
from src.utils.config import get_config


# ---------------------------------------------------------------------------
# Structured output schemas (Pydantic)
# ---------------------------------------------------------------------------

class TriageResult(BaseModel):
    """Structured output from the log triage node."""

    classification: str = Field(description="One or two sentence incident category, e.g. Network Scan (Reconnaissance)")
    mitre_technique: str = Field(description="MITRE ATT&CK technique ID and name, or N/A")
    confidence: Literal["None", "Low", "Med", "High"] = Field(description="Confidence level")
    rationale: str = Field(description="Brief evidence-based explanation")


class PlaybookSource(BaseModel):
    """A single playbook source file."""

    file: str = Field(description="Exact filename or source identifier")


class PlaybookResult(BaseModel):
    """Structured output from the playbook retrieval node."""

    playbook_name: str = Field(description="Name of the most relevant playbook")
    match_reason: str = Field(description="Why this playbook matches the incident")
    recommended_actions: List[str] = Field(description="List of recommended response actions")
    sources: List[PlaybookSource] = Field(default_factory=list, description="Source files used for retrieval")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class LogDocState(TypedDict, total=False):
    # User turn input
    user_query: str

    # Conversation history (list of {"role": str, "content": str})
    conversation_history: List[Dict[str, str]]

    # Dashboard / case context
    active_case_id: Optional[str]
    active_case_title: Optional[str]
    selected_log_data: Optional[Dict[str, Any]]

    # Existing structured outputs passed from the frontend
    triage_result: Optional[Dict[str, Any]]
    playbook_result: Optional[Dict[str, Any]]

    # Context resolver outputs
    resolved_context_status: Optional[str]   # "resolved" | "missing" | "ambiguous"
    resolved_context_notes: Optional[str]

    # Router outputs
    intent: Optional[str]
    use_existing_triage: Optional[bool]
    use_existing_playbook: Optional[bool]
    need_log_triage: Optional[bool]
    need_playbook_retrieval: Optional[bool]
    route_plan: Optional[List[str]]
    route_reason: Optional[str]

    # Final result
    final_response: Optional[str]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

CONTEXT_RESOLVER_PROMPT = """You are a case context resolver for a SOC investigation assistant.

Given the user query and any available case context, determine whether meaningful case context exists.

Active case ID: {active_case_id}
Active case title: {active_case_title}
Selected log data available: {has_log_data}
Triage result available: {has_triage}
Playbook result available: {has_playbook}
User query: {user_query}

Output a JSON object with exactly these fields:
- "resolved_context_status": one of "resolved", "missing"
- "resolved_context_notes": brief explanation

"resolved" means an active case exists and the question likely refers to it.
"missing" means no case context exists but the question needs it.

Return only the JSON object, no extra text."""


ROUTER_PROMPT = """You are the router for a SOC investigation assistant.

Your job: classify the user's intent and decide what work is needed for this turn.

Available context:
- active_case_id: {active_case_id}
- resolved_context_status: {resolved_context_status}
- triage_result exists: {has_triage}
- playbook_result exists: {has_playbook}
- user_query: {user_query}
- recent_conversation (last 4 turns): {recent_history}

Supported intents:
- general_case_question: user asks about the case in a general way
- triage_explanation: user asks why something was classified a certain way
- fresh_triage_request: user wants logs analyzed for the first time
- playbook_request: user asks for remediation/response steps
- full_investigation: user wants full analysis + remediation
- manager_summary: user wants a plain-language summary for leadership
- generic_chat: general security question not tied to the case
- missing_context: user asks a case question but no case is loaded

Routing rules:
1. If resolved_context_status is "missing" and the question is case-dependent → intent="missing_context", route_plan=["response_composer"]
2. If user asks for explanation of triage and triage exists → intent="triage_explanation", use_existing_triage=true, route_plan=["response_composer"]
3. If user asks for explanation but no triage → intent="fresh_triage_request", need_log_triage=true, route_plan=["log_triage","response_composer"]
4. If user asks for next steps / playbook and playbook exists → intent="playbook_request", use_existing_playbook=true, route_plan=["response_composer"]
5. If user asks for next steps / playbook and no playbook → intent="playbook_request", need_playbook_retrieval=true, route_plan=["playbook_retrieval","response_composer"]
6. If user asks for full analysis → intent="full_investigation", need_log_triage=true, need_playbook_retrieval=true, route_plan=["log_triage","playbook_retrieval","response_composer"]
7. If user asks for a summary / escalation summary → intent="manager_summary", route_plan=["response_composer"]
8. If general security question not requiring triage or playbook → intent="generic_chat", route_plan=["response_composer"]
9. If general case question where triage already exists → intent="general_case_question", use_existing_triage=true, route_plan=["response_composer"]

Output a JSON object with exactly these fields (all required):
{{
  "intent": "<intent>",
  "use_existing_triage": <true|false>,
  "use_existing_playbook": <true|false>,
  "need_log_triage": <true|false>,
  "need_playbook_retrieval": <true|false>,
  "route_plan": ["<node>", ...],
  "route_reason": "<one sentence>"
}}

Return only the JSON object, no extra text."""


LOG_TRIAGE_PROMPT = """You are a SOC log triage specialist. Analyze the provided log data and produce a structured triage result.

Active case: {active_case_title}
User query: {user_query}

Log data:
{log_data}

Rules:
- Do not overstate. If evidence is insufficient, set confidence to "None" or "Low".
- Do not invent details not present in the logs."""


PLAYBOOK_SYSTEM_PROMPT = """You are a playbook retrieval specialist. Given retrieved playbook content below, synthesize it into structured guidance for the incident.

Active case: {active_case_title}
User query: {user_query}
Triage classification: {classification}
MITRE technique: {mitre_technique}

Provide playbook_name, match_reason, and recommended_actions. The sources list is filled from the retrieval metadata; you may omit it or leave it empty."""


RESPONSE_COMPOSER_PROMPT = """You are the user-facing investigation assistant for LogDoc.

You help the user understand the current case by using:
- active case context
- existing triage results
- existing playbook results
- the current conversation

Rules:
- Treat structured triage and playbook outputs as the main source of truth.
- DO NOT invent technical findings not present in the case context.
- If the user asks for explanation, summarize the relevant findings clearly.
- If the user asks for remediation, use playbook guidance when available.
- If context is missing, say so clearly and ask the user to select a case or provide logs.
- Be concise, specific, and helpful.
- Distinguish between confirmed findings, likely interpretation, and uncertainty.
- If intent is "manager_summary", write in plain non-technical language suitable for leadership.

Current state:
Intent: {intent}
Context status: {resolved_context_status}
Active case: {active_case_title}

Triage result:
{triage_result}

Playbook result:
{playbook_result}

Conversation history (last 10 turns):
{conversation_history}

User question: {user_query}

Answer the user's question naturally and concisely, grounded in the state above."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> dict:
    """Extract and parse a JSON object from an LLM response (strips markdown fences)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find {} block
        m = re.search(r"\{[\s\S]+\}", text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return {}


def _format_log_data(selected_log_data: Optional[Dict[str, Any]]) -> str:
    if not selected_log_data:
        return "(no log data provided)"
    return json.dumps(selected_log_data, indent=2)


def _format_triage(triage_result: Optional[Dict[str, Any]]) -> str:
    if not triage_result:
        return "(no triage result)"
    return json.dumps(triage_result, indent=2)


def _format_playbook(playbook_result: Optional[Dict[str, Any]]) -> str:
    if not playbook_result:
        return "(no playbook result)"
    return json.dumps(playbook_result, indent=2)


def _format_history(history: Optional[List[Dict[str, str]]], n: int = 10) -> str:
    if not history:
        return "(no prior conversation)"
    tail = history[-n:]
    return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in tail)


# ---------------------------------------------------------------------------
# Node: context_resolver
# ---------------------------------------------------------------------------

def context_resolver_node(state: LogDocState) -> dict:
    """Determine whether useful case context exists for this turn."""
    config = get_config()
    llm = config.get_agent_model()

    prompt_text = CONTEXT_RESOLVER_PROMPT.format(
        active_case_id=state.get("active_case_id") or "(none)",
        active_case_title=state.get("active_case_title") or "(none)",
        has_log_data=bool(state.get("selected_log_data")),
        has_triage=bool(state.get("triage_result")),
        has_playbook=bool(state.get("playbook_result")),
        user_query=state.get("user_query") or "",
    )
    response = llm.invoke([HumanMessage(content=prompt_text)])
    parsed = _parse_json(response.content)
    return {
        "resolved_context_status": parsed.get("resolved_context_status", "missing"),
        "resolved_context_notes": parsed.get("resolved_context_notes", ""),
    }


# ---------------------------------------------------------------------------
# Node: router
# ---------------------------------------------------------------------------

def router_node(state: LogDocState) -> dict:
    """Classify intent and produce a route_plan."""
    config = get_config()
    llm = config.get_agent_model()

    prompt_text = ROUTER_PROMPT.format(
        active_case_id=state.get("active_case_id") or "(none)",
        resolved_context_status=state.get("resolved_context_status") or "missing",
        has_triage=bool(state.get("triage_result")),
        has_playbook=bool(state.get("playbook_result")),
        user_query=state.get("user_query") or "",
        recent_history=_format_history(state.get("conversation_history"), n=4),
    )
    response = llm.invoke([HumanMessage(content=prompt_text)])
    parsed = _parse_json(response.content)
    return {
        "intent": parsed.get("intent", "general_case_question"),
        "use_existing_triage": bool(parsed.get("use_existing_triage", False)),
        "use_existing_playbook": bool(parsed.get("use_existing_playbook", False)),
        "need_log_triage": bool(parsed.get("need_log_triage", False)),
        "need_playbook_retrieval": bool(parsed.get("need_playbook_retrieval", False)),
        "route_plan": parsed.get("route_plan", ["response_composer"]),
        "route_reason": parsed.get("route_reason", ""),
    }


# ---------------------------------------------------------------------------
# Node: log_triage
# ---------------------------------------------------------------------------

def log_triage_node(state: LogDocState) -> dict:
    """Analyze logs and produce structured triage_result via LLM structured output."""
    config = get_config()
    llm = config.get_specialist_model()
    structured_llm = llm.with_structured_output(TriageResult)

    prompt_text = LOG_TRIAGE_PROMPT.format(
        active_case_title=state.get("active_case_title") or "(unnamed case)",
        user_query=state.get("user_query") or "",
        log_data=_format_log_data(state.get("selected_log_data")),
    )
    result = structured_llm.invoke([HumanMessage(content=prompt_text)])
    triage_result = result.model_dump()

    # Consume log_triage from the front of route_plan
    route_plan = list(state.get("route_plan") or [])
    if route_plan and route_plan[0] == "log_triage":
        route_plan = route_plan[1:]

    return {
        "triage_result": triage_result,
        "route_plan": route_plan,
    }


# ---------------------------------------------------------------------------
# Node: playbook_retrieval
# ---------------------------------------------------------------------------

def playbook_retrieval_node(state: LogDocState) -> dict:
    """Retrieve relevant playbook guidance and produce structured playbook_result via LLM structured output."""
    config = get_config()
    llm = config.get_specialist_model()
    structured_llm = llm.with_structured_output(PlaybookResult)

    triage = state.get("triage_result") or {}
    classification = triage.get("classification", "unknown incident")
    mitre = triage.get("mitre_technique", "N/A")

    # Build a search query from triage
    query = f"{classification} {mitre}".strip()
    if not query or query == "N/A":
        query = state.get("user_query") or "incident response playbook"

    # Retrieve from knowledge base using the tool directly
    raw_retrieval = search_playbooks_knowledge_base.invoke({"query": query})

    # Parse sources out of the retrieval result (exact files from the tool)
    sources_block = ""
    guidance_text = raw_retrieval
    if "SOURCES:" in raw_retrieval.upper():
        parts = re.split(r"\n\s*SOURCES\s*:\s*\n", raw_retrieval, maxsplit=1, flags=re.IGNORECASE)
        guidance_text = parts[0].strip()
        if len(parts) > 1:
            sources_block = parts[1].strip()

    source_files = []
    for line in sources_block.splitlines():
        cleaned = line.strip().lstrip("-").strip()
        if cleaned and cleaned != "(no sources)":
            source_files.append(PlaybookSource(file=cleaned))

    # Use LLM structured output to synthesize playbook_name, match_reason, recommended_actions
    synthesis_prompt = PLAYBOOK_SYSTEM_PROMPT.format(
        active_case_title=state.get("active_case_title") or "(unnamed case)",
        user_query=state.get("user_query") or "",
        classification=classification,
        mitre_technique=mitre,
    )
    synthesis_messages = [
        SystemMessage(content=synthesis_prompt),
        HumanMessage(content=f"Retrieved playbook content:\n\n{guidance_text}"),
    ]
    result = structured_llm.invoke(synthesis_messages)
    # Use exact source files from retrieval; override any LLM-produced sources
    playbook_result = result.model_dump()
    playbook_result["sources"] = [{"file": s.file} for s in source_files]

    # Consume playbook_retrieval from route_plan
    route_plan = list(state.get("route_plan") or [])
    if route_plan and route_plan[0] == "playbook_retrieval":
        route_plan = route_plan[1:]

    return {
        "playbook_result": playbook_result,
        "route_plan": route_plan,
    }


# ---------------------------------------------------------------------------
# Node: response_composer
# ---------------------------------------------------------------------------

def response_composer_node(state: LogDocState) -> dict:
    """Generate the final user-facing response."""
    config = get_config()
    llm = config.get_agent_model()

    prompt_text = RESPONSE_COMPOSER_PROMPT.format(
        intent=state.get("intent") or "general_case_question",
        resolved_context_status=state.get("resolved_context_status") or "missing",
        active_case_title=state.get("active_case_title") or "(none)",
        triage_result=_format_triage(state.get("triage_result")),
        playbook_result=_format_playbook(state.get("playbook_result")),
        conversation_history=_format_history(state.get("conversation_history"), n=10),
        user_query=state.get("user_query") or "",
    )
    response = llm.invoke([HumanMessage(content=prompt_text)])
    return {"final_response": response.content}


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def route_from_router(state: LogDocState) -> str:
    """After router: go to first item in route_plan."""
    plan = state.get("route_plan") or ["response_composer"]
    first = plan[0] if plan else "response_composer"
    # Map to valid node names
    if first == "log_triage":
        return "log_triage"
    if first == "playbook_retrieval":
        return "playbook_retrieval"
    return "response_composer"


def route_after_log_triage(state: LogDocState) -> str:
    """After log_triage: go to playbook_retrieval if it's next, else response_composer."""
    plan = state.get("route_plan") or ["response_composer"]
    first = plan[0] if plan else "response_composer"
    if first == "playbook_retrieval":
        return "playbook_retrieval"
    return "response_composer"


# ---------------------------------------------------------------------------
# Graph build
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(LogDocState)

    graph.add_node("context_resolver", context_resolver_node)
    graph.add_node("router", router_node)
    graph.add_node("log_triage", log_triage_node)
    graph.add_node("playbook_retrieval", playbook_retrieval_node)
    graph.add_node("response_composer", response_composer_node)

    graph.add_edge(START, "context_resolver")
    graph.add_edge("context_resolver", "router")

    graph.add_conditional_edges(
        "router",
        route_from_router,
        {
            "log_triage": "log_triage",
            "playbook_retrieval": "playbook_retrieval",
            "response_composer": "response_composer",
        },
    )
    graph.add_conditional_edges(
        "log_triage",
        route_after_log_triage,
        {
            "playbook_retrieval": "playbook_retrieval",
            "response_composer": "response_composer",
        },
    )
    graph.add_edge("playbook_retrieval", "response_composer")
    graph.add_edge("response_composer", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Agent facade
# ---------------------------------------------------------------------------

_agent_instance: "LogDocAgent | None" = None


def get_logdoc_agent() -> "LogDocAgent":
    """Return the singleton LogDocAgent. Created and compiled once on first call."""
    global _agent_instance
    if _agent_instance is None:
        print("Building LogDocAgent (LogDoc graph v2)")
        _agent_instance = LogDocAgent()
    return _agent_instance


def reset_logdoc_agent() -> None:
    """Reset the LogDocAgent instance (e.g. for testing)."""
    global _agent_instance
    _agent_instance = None


class LogDocAgent:
    """Case-aware SOC investigation assistant: context_resolver → router → [log_triage] → [playbook_retrieval] → response_composer."""

    def __init__(self) -> None:
        config = get_config()
        self.llm = config.get_agent_model()
        self.graph = build_graph()

    def invoke(self, state: LogDocState) -> LogDocState:
        """Run the graph and return final state."""
        return self.graph.invoke(state, config={"recursion_limit": 10})
