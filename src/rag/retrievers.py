from operator import itemgetter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from src.utils.config import get_config
from src.utils.dataset_utils import load_documents

_naive_vector_store: QdrantVectorStore | None = None
_naive_retrieval_chain = None

RAG_PROMPT = """
You are a SOC analyst. Use the retrieved CONTEXT to help answer the QUESTION.

Guidelines:
- Prefer information from CONTEXT when available.
- If CONTEXT is missing key details, say what is missing.
- Do not fabricate specifics.

CONTEXT:
{context}

QUESTION:
{question}

Provide:
- a brief summary
- recommended actions (clear, actionable steps)
- any relevant playbook/runbook guidance from the context

Answer:
"""

def _format_docs(docs: list[Document]) -> str:
    """Format retrieved documents as a single context string for the RAG prompt."""
    return "\n\n".join(doc.page_content for doc in docs)


def _docs_to_context(d: dict) -> dict:
    """Replace raw retrieved documents with a formatted context string for the prompt."""
    return {**d, "context": _format_docs(d["context"])}


def _question_input(x: str | dict) -> dict:
    """Normalize input so the chain can be invoked with a bare question string or a dict."""
    if isinstance(x, str):
        return {"question": x}
    return x


def _create_naive_retriever(docs: list[Document], k: int = 3):

    global _naive_vector_store

    if _naive_vector_store is None:
        config = get_config()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        documents = text_splitter.split_documents(docs)

        _naive_client = QdrantClient(":memory:")
        _naive_client.create_collection(
            collection_name="soc_triage",
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        _naive_vector_store = QdrantVectorStore(
            client=_naive_client,
            collection_name="soc_triage",
            embedding=config.get_embedding_model(),
        )
        _naive_vector_store.add_documents(documents)

    return _naive_vector_store.as_retriever(search_kwargs={"k": k})


def get_naive_retriever_chain():
    """Build and return a retriever over the given docs. Client and vector store are created once and reused.

    Call with no arguments. Invoke the returned chain with a question string or a dict:
        chain = get_naive_retriever_chain()
        result = chain.invoke("What should I do about a network scan?")
        # or
        result = chain.invoke({"question": "What should I do about a network scan?"})
    """
    global _naive_retrieval_chain

    if _naive_retrieval_chain is None:
        docs = load_documents("../data/playbooks.json")

        naive_retriever = _create_naive_retriever(docs, 3)

        rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
        chat_model = get_config().get_rag_model()

        # Invoke naive_retriever with the question to get RAG documents, then format as context for the prompt
        core_chain = (
            {"context": itemgetter("question") | naive_retriever, "question": itemgetter("question")}
            | RunnableLambda(_docs_to_context)
            | {"response": rag_prompt | chat_model, "context": itemgetter("context")}
        )
        _naive_retrieval_chain = RunnableLambda(_question_input) | core_chain

    return _naive_retrieval_chain