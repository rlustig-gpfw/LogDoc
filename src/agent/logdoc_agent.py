"""
Multi-agent SOC triage system built with LangGraph.

- SOC Supervisor: LLM that reads the query/conversation and decides which specialist to use (or chat_only / end).
  Outputs structured routing. After each specialist responds, supervisor reviews and decides if playbook is needed, then response_builder.
- Log Triage Specialist: create_agent with tools; outputs classification, MITRE technique, confidence, rationale.
- Playbook Specialist: create_agent with playbook search; looks up playbook response from triage context.
- Response Builder: Assembles triage summary and playbook context for the dashboard from specialist messages.
- Chat-only: Supervisor routes here for follow-ups; LLM responds from analysis history without calling specialists.
"""

from typing import Annotated, Optional, TypedDict

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from src.agent.tools import (
    get_current_date,
    search_playbooks_knowledge_base,
    search_web,
)
from src.utils.config import OpenAIModels, get_config


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class SupervisorState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    next_step: Optional[str]


# Routing decision values (must match supervisor structured output)
ROUTE_LOG_TRIAGE = "log_triage"
ROUTE_PLAYBOOK = "playbook"
ROUTE_RESPONSE_BUILDER = "response_builder"
ROUTE_CHAT_ONLY = "chat_only"
ROUTE_END = "end"


# ---------------------------------------------------------------------------
# Specialist system prompts (structured outputs)
# ---------------------------------------------------------------------------

LOG_TRIAGE_SYSTEM = """You are a SOC log triage specialist. You help triage logs for cybersecurity-related issues.

You have access to tools: search_playbooks_knowledge_base (for playbook/runbook guidance) and search_web (for current threat info). Use get_current_date when you need the current date for time-sensitive searches.

Respond with the following items in a clear, structured way:
- **classification**: One or two sentence summary (e.g., "Benign DNS query" or "Possible C2 beaconing")
- **mitre_technique**: MITRE ATT&CK technique ID or name if applicable, otherwise "N/A"
- **confidence**: One of "None", "Low", "Med", "High"
- **rationale**: Brief evidence-based explanation

If the content is not log data or is insufficient, use classification "Insufficient data" and confidence "None". Use tools when they would improve your triage or recommended actions."""

PLAYBOOK_SYSTEM = """You are a playbook specialist. Based on the log triage analysis already in the conversation (classification, MITRE technique, rationale), search the knowledge base for the most relevant playbook(s) and incident response procedures.

Summarize the playbook guidance and recommended actions that apply to this incident. Do not re-analyze the logs; use the triage specialist's output as context. Focus on actionable steps and runbook content. Provide the playbook sources in the format: [Source: Playbook Name]"""


# ---------------------------------------------------------------------------
# Supervisor node: LLM decides next step (structured output)
# ---------------------------------------------------------------------------

SUPERVISOR_SYSTEM = """You are the SOC Supervisor. You coordinate a team of specialists by reading the conversation and deciding the next step.

**Rules:**
- If the latest user message contains logs or telemetry to analyze (or a request to analyze/triage logs), route to the log_triage specialist.
- After the log triage specialist has responded, review that response. If playbook/runbook guidance would help for this incident, route to the playbook specialist. If the triage was "Insufficient data" or clearly benign and no playbook is needed, you may route to response_builder.
- After the playbook specialist has responded (or you skipped playbook), route to response_builder to produce the final triage summary and playbook context for the dashboard.
- If the user is asking a follow-up question about a prior analysis (e.g. "why did you say that?", "what should I do first?"), do NOT call the specialist agents. Route to chat_only so the assistant answers from the conversation history only.
- If there is nothing left to do or the conversation is done, respond with "end".

**Output format:** Reply with exactly one line containing only one of these words: log_triage, playbook, response_builder, chat_only, end."""


def _supervisor_node(state: SupervisorState) -> dict:
    """LLM supervisor: read messages, output structured next_step."""
    messages = state.get("messages") or []
    config = get_config()
    llm = config.get_agent_model()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SUPERVISOR_SYSTEM),
        MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    text = (response.content if hasattr(response, "content") else str(response)).strip().lower()

    # Parse next_step from supervisor LLM response (structured: one of the route values)
    if "chat_only" in text:
        next_step = ROUTE_CHAT_ONLY
    elif "response_builder" in text:
        next_step = ROUTE_RESPONSE_BUILDER
    elif "playbook" in text:
        next_step = ROUTE_PLAYBOOK
    elif "log_triage" in text:
        next_step = ROUTE_LOG_TRIAGE
    else:
        next_step = ROUTE_END

    return {"next_step": next_step}
    

# ---------------------------------------------------------------------------
# create_agent_node: common wrapper for specialist agents
# ---------------------------------------------------------------------------

def create_agent_node(agent, name: str):
    """Create a node that runs a specialist agent and returns the final response."""

    def agent_node(state: SupervisorState) -> dict:
        print(f"[{name.upper()} Agent] Processing request...")
        result = agent.invoke({"messages": state["messages"]})
        agent_messages = result.get("messages") or []
        agent_response = agent_messages[-1] if agent_messages else None
        content = agent_response.content if agent_response and hasattr(agent_response, "content") else ""
        response_with_name = AIMessage(
            content=f"[{name.upper()} SPECIALIST]\n\n{content}",
            name=name,
        )
        print(f"[{name.upper()} Agent] Response complete.")
        return {"messages": [response_with_name]}

    return agent_node


# ---------------------------------------------------------------------------
# Specialist agents (create_agent)
# ---------------------------------------------------------------------------

def _build_log_triage_agent():
    config = get_config()
    llm = config.get_specialist_model()
    return create_agent(
        model=llm,
        tools=[get_current_date, search_playbooks_knowledge_base, search_web],
        system_prompt=LOG_TRIAGE_SYSTEM,
    )


def _build_playbook_agent():
    config = get_config()
    llm = config.get_specialist_model()
    return create_agent(
        model=llm,
        tools=[get_current_date, search_playbooks_knowledge_base, search_web],
        system_prompt=PLAYBOOK_SYSTEM,
    )


# ---------------------------------------------------------------------------
# Response builder: extract specialist content from messages and format
# ---------------------------------------------------------------------------

def _extract_specialist_content(messages: list, tag: str) -> str:
    """Get content from the last message that starts with [TAG SPECIALIST]."""
    prefix = f"[{tag.upper()} SPECIALIST]"
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            content = (m.content or "").strip()
            if content.startswith(prefix):
                body = content[len(prefix):].strip()
                return body
            if getattr(m, "name", None) == tag:
                return content
    return ""


def _response_builder_node(state: SupervisorState) -> dict:
    """Build triage summary and playbook context for dashboard from specialist messages."""
    messages = state.get("messages") or []
    triage_content = _extract_specialist_content(messages, "log_triage")
    playbook_content = _extract_specialist_content(messages, "playbook")

    summary = f"## Triage Summary\n\n{triage_content or 'N/A'}\n\n## Playbook Context\n\n{playbook_content or 'N/A'}"
    return {"messages": [AIMessage(content=summary)]}


# ---------------------------------------------------------------------------
# Chat-only node: answer from history without specialists
# ---------------------------------------------------------------------------

def _chat_only_node(state: SupervisorState) -> dict:
    """Answer follow-up questions from conversation history only (no specialist tools)."""
    config = get_config()
    llm = config.get_agent_model()
    system = (
        "You are a SOC analyst assistant. Answer the user's follow-up using only the conversation history "
        "(the prior triage summary and playbook context). Do not call any tools or specialists. Be concise and accurate."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | llm
    response = chain.invoke({"messages": state.get("messages") or []})
    content = response.content if hasattr(response, "content") else str(response)
    return {"messages": [AIMessage(content=content)]}


# ---------------------------------------------------------------------------
# Graph build
# ---------------------------------------------------------------------------

def _build_soc_graph():
    log_triage_agent = _build_log_triage_agent()
    playbook_agent = _build_playbook_agent()

    builder = StateGraph(SupervisorState)

    builder.add_node("supervisor", _supervisor_node)
    builder.add_node("log_triage_specialist", create_agent_node(log_triage_agent, "log_triage"))
    builder.add_node("playbook_specialist", create_agent_node(playbook_agent, "playbook"))
    builder.add_node("response_builder", _response_builder_node)
    builder.add_node("chat_only", _chat_only_node)

    builder.add_edge(START, "supervisor")

    def route_after_supervisor(state: SupervisorState) -> str:
        return state.get("next_step") or ROUTE_END

    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            ROUTE_LOG_TRIAGE: "log_triage_specialist",
            ROUTE_PLAYBOOK: "playbook_specialist",
            ROUTE_RESPONSE_BUILDER: "response_builder",
            ROUTE_CHAT_ONLY: "chat_only",
            ROUTE_END: END,
        },
    )
    builder.add_edge("log_triage_specialist", "supervisor")
    builder.add_edge("playbook_specialist", "supervisor")
    builder.add_edge("response_builder", END)
    builder.add_edge("chat_only", END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Agent facade
# ---------------------------------------------------------------------------

_agent_instance: "LogDocAgent | None" = None


def get_logdoc_agent() -> "LogDocAgent":
    """Return the singleton LogDocAgent. Created and compiled once on first call."""
    global _agent_instance
    if _agent_instance is None:
        print("Building LogDocAgent (multi-agent SOC graph)")
        _agent_instance = LogDocAgent()
    return _agent_instance


def reset_logdoc_agent() -> None:
    """Reset the LogDocAgent instance."""
    global _agent_instance
    _agent_instance = None


class LogDocAgent:
    """Multi-agent SOC triage: LLM supervisor + log triage specialist + playbook specialist + response builder"""

    def __init__(self) -> None:
        config = get_config()
        self.llm = config.get_agent_model()
        self.graph = _build_soc_graph()

    def invoke(
        self,
        messages: list[BaseMessage] | None = None,
        *,
        single_message: str | None = None,
    ) -> str:
        """Run the graph and return the final assistant content."""
        if single_message is not None:
            messages = [HumanMessage(content=single_message)]
        if not messages:
            return ""
        state: SupervisorState = {"messages": messages}
        result = self.graph.invoke(state, config={"recursion_limit": 12})
        out_messages = result.get("messages") or []
        last = next((m for m in reversed(out_messages) if isinstance(m, AIMessage)), None)
        return (last.content or "") if last else ""
