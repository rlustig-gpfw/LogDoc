"""
Utilities to extract incident response playbooks from websites and PDFs,
and to save/load them as LangChain Documents.
"""

import json
from pathlib import Path

import pymupdf4llm

from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader


def extract_from_urls(urls: list[str]) -> list[Document]:
    """
    Extract text from web pages and return them as Documents.

    Args:
        urls: List of URLs to fetch (e.g. playbook pages).

    Returns:
        List of Documents with page_content and metadata (source URL, title, etc.).
    """
    if not urls:
        return []
    loader = WebBaseLoader(urls)
    return loader.load()


def extract_from_pdf(path: str) -> list[Document]:
    """
    Extract text from a single PDF file. Each page becomes one Document.

    Args:
        path: Path to the PDF file.

    Returns:
        List of Documents (one per page) with page_content and metadata.
    """
    path = Path(path)
    if not path.suffix.lower() == ".pdf":
        raise ValueError(f"Expected a PDF file, got: {path}")
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    markdown = pymupdf4llm.to_markdown(path)
    return [Document(page_content=markdown, metadata={"source": str(path)})]


def extract_from_pdfs(paths: list[str]) -> list[Document]:
    """
    Extract text from multiple PDF files. Pages from all files are concatenated.

    Args:
        paths: List of paths to PDF files.

    Returns:
        List of Documents from all PDFs (one Document per page).
    """
    if not paths:
        return []
    all_docs: list[Document] = []
    for path in paths:
        all_docs.extend(extract_from_pdf(path))
    return all_docs


def extract_playbooks(
    urls: list[str] | None = None,
    pdf_paths: list[str] | list[Path] | None = None,
) -> list[Document]:
    """
    Extract incident response playbooks from websites and/or PDFs into Documents.

    Args:
        urls: Optional list of URLs to scrape (e.g. playbook pages).
        pdf_paths: Optional list of paths to PDF files.

    Returns:
        Combined list of Documents from all sources. Web pages and PDF pages
        are included with metadata (source URL or file path, etc.).
    """
    docs: list[Document] = []
    if urls:
        docs.extend(extract_from_urls(urls))
    if pdf_paths:
        docs.extend(extract_from_pdfs(list(pdf_paths)))
    return docs


def save_documents(docs: list[Document], path: str | Path) -> None:
    """
    Save a list of Documents to a JSON file.

    Each document is stored as {"page_content": str, "metadata": dict}.
    Metadata values must be JSON-serializable.

    Args:
        docs: List of LangChain Documents to save.
        path: Output file path (typically .json).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {"page_content": d.page_content, "metadata": d.metadata}
        for d in docs
    ]
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_documents(path: str | Path) -> list[Document]:
    """
    Load Documents from a JSON file produced by save_documents.

    Args:
        path: Path to the JSON file.

    Returns:
        List of LangChain Documents with page_content and metadata restored.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Document store not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        records = json.load(f)
    return [
        Document(page_content=r["page_content"], metadata=r.get("metadata", {}))
        for r in records
    ]


if __name__ == "__main__":
    docs = extract_playbooks(
        # urls=[
        #     "https://docs.lumu.io/portal/en/kb/articles/network-scan-response-playbook",
        #     "https://docs.lumu.io/portal/en/kb/articles/network-bruteforce-ir-playbook",
        # ],
        pdf_paths=[
            "data/kb/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf",
            "data/kb/NIST.SP.800-61r2.pdf",
            "data/kb/network-scan-response-playbook.pdf",
            "data/kb/network-bruteforce-ir-playbook.pdf",
        ],
    )
    output_path = "data/playbooks.json"
    save_documents(docs, output_path)
    print(f"Saved {len(docs)} documents to {output_path}")
