

from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter
from utils.config import get_config
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore


def get_naive_retriever(docs: list[Document], k: int = 3):

    config = get_config()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = text_splitter.split_documents(docs)

    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name="soc_triage",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name="soc_triage",
        embedding=config.get_embedding_model(),
    )

    _ = vector_store.add_documents(documents)

    return vector_store.as_retriever(search_kwargs={"k": k})
