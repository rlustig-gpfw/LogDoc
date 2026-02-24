"""
Manages the various configuration settings for the project,
including API keys, embedding model, LLM models, and the Qdrant vector store/retriever.
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import QdrantClient

load_dotenv()


class OpenAIModels:
    """OpenAI model ids used across the project."""

    agent: str = "gpt-4o-mini"           # Main triage agent
    sdg: str = "gpt-4o-mini"             # Synthetic data generation
    ragas: str = "gpt-4o-mini"           # Ragas evaluation


class Config:
    """API keys and embedding model. Values read from environment (e.g. .env)."""

    def __init__(self):
        self._openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self._embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    def get_embedding_model(self) -> OpenAIEmbeddings:
        return self._embedding_model

    def get_agent_model(self) -> ChatOpenAI:
        return ChatOpenAI(model=OpenAIModels.agent)

    def get_sdg_model(self) -> ChatOpenAI:
        return ChatOpenAI(model=OpenAIModels.sdg)

    def get_ragas_model(self) -> ChatOpenAI:
        return ChatOpenAI(model=OpenAIModels.ragas)


def get_config() -> Config:
    """Return the shared Config instance (created once)."""
    if get_config._instance is None:
        get_config._instance = Config()
    return get_config._instance






