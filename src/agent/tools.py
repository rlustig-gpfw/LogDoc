"""
Tools for the LangChain agent to use for searching the RAG knowledge base and web.
"""

from datetime import datetime, timezone

from langchain.tools import tool
from langchain_tavily import TavilySearch

from src.rag.retrievers import get_naive_retriever_chain


@tool
def get_current_date() -> str:
    """
    Return today's date (year, month, day) in the system's timezone. 
    
    Call this when you need to know the current date or year.
    For example, before formulating a web search for "latest" or "current" information, so you can include the correct current year in the search query instead of guessing.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d (%B %d, %Y)")


def _source_id(doc) -> str:
    """Get a display name for the document source (file path or identifier)."""
    if hasattr(doc, "metadata") and doc.metadata:
        return (
            doc.metadata.get("source")
            or doc.metadata.get("file_path")
            or doc.metadata.get("title")
        ) or "unknown"
    return "unknown"


@tool
def search_playbooks_knowledge_base(query: str) -> str:
    """
    Search the local knowledge base for playbooks and documentation about network security incidents and recommended actions. The knowledge base contains ingested runbooks/playbooks only; it does not have real-time or "latest" web content.

    Use this tool to:
    - get network security playbooks and incident response procedures
    - triage and troubleshoot a network security incident
    - get general network security guidance from the playbooks

    For current events, latest trends, or topics not well covered in playbooks, also use search_web (and get_current_date if the query is time-sensitive).
    """
    retriever = get_naive_retriever_chain()
    print(f"playbooks query: {query}")
    result = retriever.invoke(query)
    response_text = result.get("response") or ""
    docs = result.get("context") or []
    sources = list(dict.fromkeys(_source_id(d) for d in docs))  # unique, order preserved
    sources_block = "\n".join(f"- {s}" for s in sources) if sources else "- (no sources)"
    out = f"{response_text}\n\nSOURCES:\n{sources_block}"
    # print(f"search_playbooks_knowledge_base result length={len(response_text)}, sources={len(sources)}")
    return out
    

@tool
def search_web(query: str) -> str:
    """
    Search the web for current information about cybersecurity.
    
    Use this tool to:
    - find new playbooks or documentation not included in the local knowledge base
    - find information about new cybersecurity incidents, threats, or trends
    - answer questions about recent events, current year guidance, or "latest" anything
    
    When the user asks for latest or current information, call get_current_date first to get the actual current year, then include that year (and terms like "latest" or "recent") in your search query so results are up-to-date.
    
    If the query is not related to cybersecurity, you should not use this tool.
    """
    search_tool = TavilySearch(
        max_results=3,
        topic="general",
        include_images=False
    )
    search_results = search_tool.run(query)
    print(f"search_web result: {search_results}")
    return search_results
