"""
Manages the various configuration settings for the project,
including API keys, embedding model, LLM models, and the Qdrant vector store/retriever.
"""

import os

#from dotenv import load_dotenv
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import QdrantClient


_config = None

def get_config() -> "Config":
    """Return the shared Config instance (created once)."""
    global _config
    if _config is None:
        _config = Config()
    return _config

class OpenAIModels:
    """OpenAI model ids used across the project."""

    agent: str = "gpt-4.1"           # Main triage agent
    rag: str = "gpt-4.1-mini"             # RAG retrieval - need a more powerful model to retrieve the relevant documents
    sdg: str = "gpt-4.1-mini"             # Synthetic data generation
    evaluator: str = "gpt-4.1"       # Ragas evaluation - need a more powerful model to evaluate the SDG data


class Config:
    """API keys and embedding model. Values read from environment (e.g. .env)."""

    def __init__(self):
        self._openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self._tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        self._cohere_api_key = os.getenv("COHERE_API_KEY", "")
        self._embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

        self._agent_model = None
        self._rag_model = None
        self._sdg_model = None
        self._evaluator_model = None

    def get_embedding_model(self) -> OpenAIEmbeddings:
        return self._embedding_model

    def get_agent_model(self) -> ChatOpenAI:
        if self._agent_model is None:
            self._agent_model = ChatOpenAI(model=OpenAIModels.agent)
        return self._agent_model

    def get_sdg_model(self) -> ChatOpenAI:
        if self._sdg_model is None:
            rate_limiter = InMemoryRateLimiter(
                requests_per_second=2, check_every_n_seconds=0.1, max_bucket_size=1
            )
            self._sdg_model = ChatOpenAI(
                model=OpenAIModels.sdg,
                temperature=0,
                max_tokens=3000,
                rate_limiter=rate_limiter,
            )
        return self._sdg_model

    def get_rag_model(self) -> ChatOpenAI:
        if self._rag_model is None:
            self._rag_model = ChatOpenAI(model=OpenAIModels.rag)
        return self._rag_model

    def get_evaluator_model(self) -> ChatOpenAI:
        if self._evaluator_model is None:
            rate_limiter = InMemoryRateLimiter(
                requests_per_second=2, check_every_n_seconds=0.1, max_bucket_size=1
            )
            self._evaluator_model = ChatOpenAI(
                model=OpenAIModels.evaluator,
                rate_limiter=rate_limiter,
            )
        return self._evaluator_model

