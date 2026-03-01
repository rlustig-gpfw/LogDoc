import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd

from langchain_openai import OpenAIEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.testset import Testset, TestsetGenerator
from ragas.testset.persona import Persona
from src.utils.config import get_config
from src.utils.dataset_utils import load_documents


def _sanitize_json_escapes(raw: str) -> str:
    """
    Fix invalid JSON escape sequences in LLM output so Pydantic can parse it.
    Valid JSON escapes are \\\", \\\\, \\/, \\b, \\f, \\n, \\r, \\t, \\uXXXX.
    Invalid escapes (e.g. \\S in "Security Agency") cause ValidationError.
    """
    # Replace \X with X when X is not a valid escape char (leave \u for \uXXXX)
    sanitized = re.sub(r'\\([^"\\/bfnrtu])', r'\1', raw)
    # Fix \u that isn't followed by exactly 4 hex digits (invalid \u9, \u12, etc.)
    sanitized = re.sub(r'\\u(?!([0-9a-fA-F]{4}))', r'u', sanitized)
    return sanitized


def _apply_ragas_json_sanitizer():
    """
    Monkey-patch Pydantic so LLM JSON with invalid escapes is sanitized before parsing.
    Restored after generate_golden_dataset so the rest of the app is unaffected.
    """
    from pydantic import BaseModel

    _original_validate_json = BaseModel.model_validate_json
    # Get the underlying function (unbound); the bound method only takes (json_data).
    _original_func = getattr(_original_validate_json, "__func__", _original_validate_json)

    @classmethod
    def _sanitized_model_validate_json(cls, json_data: str, **kwargs):
        if isinstance(json_data, str):
            json_data = _sanitize_json_escapes(json_data)
        return _original_func(cls, json_data, **kwargs)

    BaseModel.model_validate_json = _sanitized_model_validate_json
    return _original_validate_json


def chunk_docs(docs: list[Document], chunk_size: int = 4000, chunk_overlap: int = 300) -> list[Document]:
    """
    Chunk documents into smaller documents for SDG generation.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(docs)


def get_personas() -> list[str]:
    """
    Get the personas for the golden dataset.
    """
    persona_new_soc_analyst = Persona(
        name="New SOC Analyst",
        role_description="A new SOC analyst who is just starting out and needs to learn the ropes.",
    )
    
    persona_senior_soc_analyst = Persona(
        name="Senior SOC Analyst",
        role_description="A senior SOC analyst who has a lot of experience and wants to know the latest and greatest in cybersecurity.",
    )

    persona_triage_support_analyst = Persona(
        name="Triage Support Analyst",
        role_description="Wants to know the best ways to triage issues and how to act on them.",
    )

    return [persona_new_soc_analyst, persona_senior_soc_analyst, persona_triage_support_analyst]


def generate_golden_dataset() -> Testset:
    """
    Generate a golden dataset of questions, answers, and context for RAGAS evaluation.
    """
    import os
    from pydantic import BaseModel

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    playbooks_path = os.path.join(project_root, "data", "playbooks4.json")

    # Patch Pydantic to fix invalid JSON escapes from the LLM (e.g. NEROutput "entities")
    original_validate_json = _apply_ragas_json_sanitizer()
    try:
        config = get_config()
        sdg_llm = config.get_sdg_model()
        sdg_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

        generator = TestsetGenerator(
            llm=sdg_llm,
            embedding_model=sdg_embeddings,
            persona_list=get_personas()
        )

        docs = load_documents(playbooks_path)
        chunks = chunk_docs(docs, chunk_size=4000, chunk_overlap=300)
        dataset = generator.generate_with_chunks(
            chunks=chunks,
            testset_size=10,
        )
        # dataset = generator.generate_with_langchain_docs(
        #     documents=docs,
        #     testset_size=10,
        # )

        return dataset
    finally:
        BaseModel.model_validate_json = original_validate_json

def save_dataset(dataset: Testset, path: str) -> None:
    """
    Save a dataset to a JSON file.
    """
    df = dataset.to_pandas()
    df.to_json(path, orient="records")
    print(f"Saved dataset to {path}")

def load_dataset(path: str) -> Testset:
    """
    Load a dataset from a JSON file.
    """
    df = pd.read_json(path, orient="records", dtype_backend="numpy_nullable")
    return Testset.from_pandas(df)
    # import json
    # with open(path, "r") as f:
    #     data = json.load(f)
    #     return Testset.from_list(data)


if __name__ == "__main__":


    dataset2 = load_dataset("data/sdg/sdg_dataset.json")
    ttt = 0