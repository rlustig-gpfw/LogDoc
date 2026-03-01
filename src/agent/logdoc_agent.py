from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.agents import create_agent

from src.agent.tools import get_current_date, search_playbooks_knowledge_base, search_web
from src.utils.config import OpenAIModels, get_config


_agent_instance: "LogDocAgent | None" = None


def get_logdoc_agent() -> "LogDocAgent":
    """Return the singleton LogDocAgent. Created and compiled once on first call."""
    global _agent_instance
    if _agent_instance is None:
        print(f"Building LogDocAgent")
        _agent_instance = LogDocAgent()
    return _agent_instance

def reset_logdoc_agent() -> None:
    """Reset the LogDocAgent instance."""
    global _agent_instance
    _agent_instance = None

class LogDocAgent:
    """ The LogDocAgent for SOC triage analysis """
    
    def __init__(self):
        """ Initialize the LogDocAgent """
        config = get_config()
        self.llm = config.get_agent_model()
        self.tools = [get_current_date, search_playbooks_knowledge_base, search_web]
        self.graph = self._build_agent()

    def _build_agent(self):
        SYSTEM_PROMPT = """
        You are a Security Operations Center (SOC) analyst. You answer questions related to cybersecurity and SOC operations for fellow analysts.

        **Scope**: you MUST only answer cyber and security related questions. Supporting topics include:
        - Security incident triage and analysis (e.g., Zeek-style or other network telemetry, logs, alerts)
        - Playbooks for detecting, triaging, and responding to security incidents
        - General SOC, detection, and response guidance

        If the user asks about something that is NOT cyber- or security-related (e.g., general IT, off-topic, or non-security questions), do not answer the substance of the question.
        Instead respond clearly that you only answer cybersecurity and Security Operations Center related questions, and that the question is out of scope. You are not a generalist.

        Rules when answering in-scope questions:
        - You can and should call multiple tools when a question needs it. Do not stop after one tool call if the answer would be better with more sources. For example: call the knowledge base for playbook guidance, then call search_web for current or recent information, then synthesize both.
        - Use the knowledge base to look up playbooks or documentation that support your recommended actions.
        - Also call search_web when: the user asks for "latest", "current", or "recent" information; the topic is an emerging threat or new technology (e.g., AI abuse, MCP); or the knowledge base results do not clearly cover the question. For recency-sensitive searches, call get_current_date first, then include that year in your search_web query.
        - If the information you already retrieved is not sufficient, call the same or another tool again with a different or more specific query.

        Your first action should be to use the tools to retrieve the most relevant information. After reviewing tool results, call additional tools if needed before giving your final answer.
        
        For incident or triage-style queries (e.g., user provides logs or asks "what happened?" about an incident), provide a classification, mitre_technique, rationale, and recommended_actions.

        For other in-scope questions (e.g., general security concepts, how to use a playbook, or what to do for a type of incident), respond in a clear, helpful way and prefer to use tools when relevant.

        Format the response with a clear structure with headings, formatting, and numbered or bulleted lists.
        """
        
        agent = create_agent(
            model=OpenAIModels.agent,
            tools=self.tools,
            system_prompt=SYSTEM_PROMPT
        )
        return agent

    def invoke(self, messages: str) -> BaseMessage:
        """ Invoke the agent with the given messages """
        response = self.graph.invoke(
            {
                "messages": [HumanMessage(content=messages)]
            },
            config={
                "recursive_call": 5
            }
        )
        
        for msg in response["messages"]:
            msg_type = type(msg).__name__
            content = msg.content if msg.content else f"[Tool calls: {msg.tool_calls}]" if hasattr(msg, 'tool_calls') and msg.tool_calls else "[No content]"
            print(f"  [{msg_type}]: {content}")

        output_message = response["messages"][-1]
        return output_message.content
