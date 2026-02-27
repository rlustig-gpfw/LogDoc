from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.agents import create_agent

from src.agent.tools import search_playbooks_knowledge_base, search_web
from src.utils.config import OpenAIModels, get_config


# def LogDocState(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]


_agent_instance: "LogDocAgent | None" = None


def get_logdoc_agent() -> "LogDocAgent":
    """Return the singleton LogDocAgent. Created and compiled once on first call."""
    print(f"get_logdoc_agent")
    global _agent_instance
    if _agent_instance is None:
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
        self.tools = [search_playbooks_knowledge_base, search_web]
        self.graph = self._build_agent()

    def _build_agent(self):
        SYSTEM_PROMPT = """
        You are a Security Operations Center (SOC) analyst. You answer questions related to cybersecurity and SOC operations for fellow analysts.

        Scope — you MUST only answer cyber and security related questions. Supporting topics include:
        - Security incident triage and analysis (e.g., Zeek-style or other network telemetry, logs, alerts)
        - Playbooks for detecting, triaging, and responding to security incidents
        - General SOC, detection, and response guidance

        If the user asks about something that is NOT cyber- or security-related (e.g., general IT, off-topic, or non-security questions), do not answer the substance of the question.
        Instead respond clearly that you only answer cybersecurity and Security Operations Center related questions, and that the question is out of scope. You are not a generalist.

        Rules when answering in-scope questions:
        - Use the tools provided to look up playbooks or documentation that support your recommended actions. If the information you already retrieved is not sufficient, call the tool again with a different or more specific query.

        Your first action should be to use the tools to retrieve the most relevant information, playbooks, or documentation.
        
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




# def get_logdoc_agent() -> "LogDocAgent":
#     """Return the singleton LogDocAgent. Created and compiled once on first call."""
#     global _agent_instance
#     if _agent_instance is None:
#         _agent_instance = LogDocAgent()
#         _agent_instance.build_graph()
#     return _agent_instance

# class LogDocAgent:
#     """ The LogDocAgent for SOC triage analysis """
    
#     def __init__(self):
#         """ Initialize the LogDocAgent """
#         config = get_config()
#         self.llm = config.get_agent_model()
#         self.tools = [search_playbooks_knowledge_base, search_web]
#         self.graph = None

#     # New node to process input query from user (including Zeek logs) or handle tool calls if agent loop needs more tool calls
#     def _analyze(self, state: LogDocState) -> LogDocState:
#         """ Analyze the input query from user (including Zeek logs) or handle tool calls if agent loop needs more tool calls """

#         SYSTEM_PROMPT = """
#         You are a Security Operations Center (SOC) analyst. Your objective is to triage Zeek-style network telemetry and produce a concise SOC-style assessment and recommended response for a fellow analyst.

#         Rules:
#         - Base all conclusions on evidence from the provided telemetry. Cite specific log fields or events when explaining your reasoning.
#         - If the data is insufficient to classify or attribute activity, do not speculate. Use "unknown" for classification or mitre_technique and set confidence to "low"; in rationale, state "Insufficient evidence" and what would be needed to decide.
#         - Use the tools provided to look up runbooks, playbooks, or documentation that support your recommended actions. If the information you already retrieved is not sufficient, call the tool again with a different or more specific query.

#         Your output must answer: (1) What happened? (2) Why it matters? (3) What to do?

#         Return your response as valid JSON with exactly these fields:
#         {
#             "classification": "benign | suspicious | malicious | unknown",
#             "mitre_technique": "MITRE ATT&CK technique ID and name if applicable, or null/empty if none or unknown",
#             "rationale": "Evidence-based explanation grounded in the telemetry; what you observed and why it led to this classification",
#             "recommended_actions": "Concrete next steps (e.g., isolate host, escalate, collect more logs); use runbook/playbook guidance as a primary source of information when available",
#             "confidence": "low | medium | high"
#         }
#         """
#         messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
#         response = self.llm.bind_tools(self.tools).invoke(messages)
#         return {"messages": [response]}

#     # Determine whether to call tools or end the conversation
#     def _should_continue(state: LogDocState) -> Literal["tools", "end"]:
#         """Determine whether to call tools or end the conversation."""
#         last_message = state["messages"][-1]
        
#         # If the LLM made tool calls, route to tools node
#         if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
#             return "tools"
        
#         # Otherwise, end the conversation
#         return "end"

#     def _build_graph(self):
#         """ Build the graph for the LogDocAgent """
#         graph_builder = StateGraph(LogDocState)
#         graph_builder.add_node("analyze", self._analyze)
#         graph_builder.add_node("tools", self.tools)

#         graph_builder.add_edge(START, "analyze")
#         graph_builder.add_conditional_edges(
#             "analyze",
#             self.should_continue,
#             {
#                 "tools": "tools",
#                 "end": END
#             }
#         )
#         graph_builder.add_edge("tools", "analyze")

#         self.graph = graph_builder.compile()

#     def get_agent(self):
#         """ Get the agent for the LogDocAgent """
#         return self.graph
    