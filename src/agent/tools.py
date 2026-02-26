"""
Tools for the LangChain agent to use for searching the RAG knowledge base and web.
"""

from langchain.tools import tool
from langchain_tavily import TavilySearch

from src.rag.retrievers import get_naive_retriever_chain


@tool
def search_playbooks_knowledge_base(query: str) -> str:
    """
    Search the local knowledge base for the information about network security incidents and recommended actions.

    Use this tool to:
    - provide network security playbooks
    - triage and troubleshoot a network security incident
    - provide general network security guidance
    """
    retriever = get_naive_retriever_chain()
    result = retriever.invoke(query)
    return result["response"]
    

@tool
def search_web(query: str) -> str:
    """
    Search the web for information about cybersecurity incidents and recommended actions.
    
    Use this tool to:
    - find new playbooks or documentation not included in the local knowledge base
    - find information about new cybersecurity incidents or trends
    
    If the query is not related to cybersecurity, you should not use this tool.
    """
    search_tool = TavilySearch(
        max_results=3,
        topic="general",
        include_images=False
    )
    search_results = search_tool.run(query)
    return search_results
