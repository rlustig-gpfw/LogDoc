from langchain_core.messages import BaseMessage, SystemMessage
from typing_extensions import Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_qdrant import QdrantRAG
from langchain.tools import Tool
from langchain_core.messages import add_messages
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict


def LogDocState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

class LogDocAgent:
    """ The LogDocAgent for SOC triage analysis """
    
    def __init__(self):
        """ Initialize the LogDocAgent """
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.rag = QdrantRAG(collection_name="log_doc")
        self.tools = [
            Tool(
                name="log_doc",
                func=self.rag.search,
                description="Search the log_doc collection for relevant information"
            )
        ]

    # New node to process input query from user (including Zeek logs) or handle tool calls if agent loop needs more tool calls
    def _analyze(self, state: LogDocState) -> LogDocState:
        """ Analyze the input query from user (including Zeek logs) or handle tool calls if agent loop needs more tool calls """

        SYSTEM_PROMPT = """
        You are a Security Operations Center (SOC) analyst. Your objective is to triage Zeek-style network telemetry and produce a concise SOC-style assessment and recommended response for a fellow analyst.

        Rules:
        - Base all conclusions on evidence from the provided telemetry. Cite specific log fields or events when explaining your reasoning.
        - If the data is insufficient to classify or attribute activity, do not speculate. Use "unknown" for classification or mitre_technique and set confidence to "low"; in rationale, state "Insufficient evidence" and what would be needed to decide.
        - Use the tools provided to look up runbooks, playbooks, or documentation that support your recommended actions. If the information you already retrieved is not sufficient, call the tool again with a different or more specific query.

        Your output must answer: (1) What happened? (2) Why it matters? (3) What to do?

        Return your response as valid JSON with exactly these fields:
        {
            "classification": "benign | suspicious | malicious | unknown",
            "mitre_technique": "MITRE ATT&CK technique ID and name if applicable, or null/empty if none or unknown",
            "rationale": "Evidence-based explanation grounded in the telemetry; what you observed and why it led to this classification",
            "recommended_actions": "Concrete next steps (e.g., isolate host, escalate, collect more logs); use runbook/playbook guidance as a primary source of information when available",
            "confidence": "low | medium | high"
        }
        """
        # Provide all messages to the model so the model sees user message, any prior tool calls, and tool results and can decide to call tools again or respond
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
        response = self.llm.bind_tools(self.tools).invoke(messages)
        return {"messages": [response]}

    # Determine whether to call tools or end the conversation
    def should_continue(state: LogDocState) -> Literal["tools", "end"]:
        """Determine whether to call tools or end the conversation."""
        last_message = state["messages"][-1]
        
        # If the LLM made tool calls, route to tools node
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # Otherwise, end the conversation
        return "end"

    def build_graph(self):
        """ Build the graph for the LogDocAgent """
        graph_builder = StateGraph(LogDocState)
        graph_builder.add_node("analyze", self._analyze)
        graph_builder.add_node("tools", self.tools)

        graph_builder.add_edge(START, "analyze")
        graph_builder.add_conditional_edges(
            "analyze",
            self.should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        graph_builder.add_edge("tools", "analyze")

        graph = graph_builder.compile()
        return graph
    