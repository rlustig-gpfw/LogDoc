from operator import itemgetter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.stores import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from langchain_classic.retrievers import ContextualCompressionRetriever, ParentDocumentRetriever

from langchain_cohere import CohereRerank

from src.utils.config import get_config
from src.utils.dataset_utils import load_documents


_naive_retrieval_chain = None
_contextual_compression_retrieval_chain = None
_parent_document_retrieval_chain = None

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
- citations to the information sources used to answer the question

Answer:
"""

def _question_input(x: str | dict) -> dict:
    """Normalize input so the chain can be invoked with a bare question string or a dict."""
    if isinstance(x, str):
        return {"question": x}
    return x

def _load_playbooks() -> list[Document]:
    """
    Load the playbooks from the data directory.
    Tries to load various paths in the data directory, which depends on the current working directory.
    """
    potential_playbook_paths = [
        "data/playbooks.json",
        "../data/playbooks.json",
        "../../data/playbooks.json",
    ]
    for playbook_path in potential_playbook_paths:
        try:
            docs = load_documents(playbook_path)
            print(f"Loaded {len(docs)} playbooks from {playbook_path}")
            return docs
        except FileNotFoundError:
            continue

    print(f"No playbooks found in {potential_playbook_paths}")
    raise FileNotFoundError(f"No playbooks found in {potential_playbook_paths}") from None

def _create_naive_retriever(docs: list[Document], k: int = 3):
    """
    Create a naive retriever over the given documents.
    """
    config = get_config()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=300,
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
    print(f"Added {len(documents)} documents to the vector store")

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

        docs = _load_playbooks()

        naive_retriever = _create_naive_retriever(docs, 3)

        rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
        chat_model = get_config().get_rag_model()

        # Invoke naive_retriever with the question to get RAG documents, then format as context for the prompt
        core_chain = (
            {"context": itemgetter("question") | naive_retriever, "question": itemgetter("question")}
            # | RunnableLambda(_docs_to_context)
            | RunnablePassthrough.assign(context=itemgetter("context"))
            | {"response": rag_prompt | chat_model, "context": itemgetter("context")}
        )
        _naive_retrieval_chain = RunnableLambda(_question_input) | core_chain

    return _naive_retrieval_chain

def _create_contextual_compression_retriever(docs: list[Document], k: int = 3):
    """Create a contextual compression retriever over the given docs."""

    compressor = CohereRerank(model="rerank-v3.5")
    contextual_compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=_create_naive_retriever(docs, k)
    )
    return contextual_compression_retriever

def get_contextual_compression_retriever_chain():
    """Build and return a contextual compression retriever over the given docs. Client and vector store are created once and reused.

    Call with no arguments. Invoke the returned chain with a question string or a dict:
        chain = get_contextual_compression_retriever_chain()
        result = chain.invoke("What should I do about a network scan?")
        # or
        result = chain.invoke({"question": "What should I do about a network scan?"})
    """
    global _contextual_compression_retrieval_chain

    if _contextual_compression_retrieval_chain is None:

        docs = _load_playbooks()

        contextual_compression_retriever = _create_contextual_compression_retriever(docs, 10)

        rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
        chat_model = get_config().get_rag_model()

        core_chain = (
            {"context": itemgetter("question") | contextual_compression_retriever, "question": itemgetter("question")}
        #    | RunnableLambda(_docs_to_context)
            | RunnablePassthrough.assign(context=itemgetter("context"))
            | {"response": rag_prompt | chat_model, "context": itemgetter("context")}
        )
        _contextual_compression_retrieval_chain = RunnableLambda(_question_input) | core_chain

    return _contextual_compression_retrieval_chain


def _create_parent_document_retriever(docs: list[Document]):
    """Create a parent-child retriever over the given docs."""

    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

    client = QdrantClient(location=":memory:")
    client.create_collection(
        collection_name="soc_triage_parent_child",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )
    parent_document_vectorstore = QdrantVectorStore(
        collection_name="soc_triage_parent_child",
        embedding=get_config().get_embedding_model(),
        client=client
    )

    store = InMemoryStore()
    parent_document_retriever = ParentDocumentRetriever(
        vectorstore=parent_document_vectorstore,
        docstore=store,
        parent_splitter=parent_splitter,
        child_splitter=child_splitter,
    )

    parent_document_retriever.add_documents(docs)
    
    return parent_document_retriever

def get_parent_document_retriever_chain():
    """Build and return a parent-document retriever over the given docs. Client and vector store are created once and reused.

    Call with no arguments. Invoke the returned chain with a question string or a dict:
        chain = get_parent_document_retriever_chain()
        result = chain.invoke("What should I do about a network scan?")
        # or
        result = chain.invoke({"question": "What should I do about a network scan?"})
    """
    global _parent_document_retrieval_chain

    if _parent_document_retrieval_chain is None:

        docs = _load_playbooks()

        parent_document_retriever = _create_parent_document_retriever(docs)

        rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
        chat_model = get_config().get_rag_model()

        core_chain = (
            {"context": itemgetter("question") | parent_document_retriever, "question": itemgetter("question")}
            | RunnablePassthrough.assign(context=itemgetter("context"))
            | {"response": rag_prompt | chat_model, "context": itemgetter("context")}
        )
        _parent_document_retrieval_chain = RunnableLambda(_question_input) | core_chain

    return _parent_document_retrieval_chain
