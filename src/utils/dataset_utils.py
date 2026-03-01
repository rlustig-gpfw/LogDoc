"""
Utilities to extract incident response playbooks from websites and PDFs,
and to save/load them as LangChain Documents.
"""

import json
from pathlib import Path

import pymupdf4llm

from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader


import re
import unicodedata

# def clean_extracted_text(text: str) -> str:
#     if not text:
#         return ""

#     # Remove ASCII control chars except: \n \r \t
#     CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

#     # Remove common zero-width / directional markers
#     ZERO_WIDTH = re.compile(r"[\u200B-\u200F\u202A-\u202E\u2060\uFEFF]")

#     MULTI_SPACE = re.compile(r"[ \t]{2,}")
#     MULTI_NEWLINE = re.compile(r"\n{3,}")

#     text = unicodedata.normalize("NFKC", text)
#     text = text.replace("\r\n", "\n").replace("\r", "\n")
#     text = CONTROL_CHARS.sub("", text)     # ✅ fixes your error
#     text = ZERO_WIDTH.sub("", text)
#     text = MULTI_SPACE.sub(" ", text)
#     text = MULTI_NEWLINE.sub("\n\n", text)
#     return text.strip()

# def extract_plain_text(pdf_path: str) -> str:
#     import fitz
#     pdf_path = Path(pdf_path)
#     doc = fitz.open(pdf_path)
#     parts = []
#     for page in doc:
#         parts.append(page.get_text("text"))
#     return "\n".join(parts)

# Remove ASCII control chars except \n \r \t
DISALLOWED_ASCII_CONTROLS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

ALLOWED_WHITESPACE = {"\n", "\r", "\t"}


def strip_unicode_controls(text: str) -> str:
    """
    Remove all Unicode control/format/private-use/surrogate characters.
    Keeps normal printable characters and standard whitespace.
    """
    cleaned = []
    for ch in text:
        if ch in ALLOWED_WHITESPACE:
            cleaned.append(ch)
            continue

        category = unicodedata.category(ch)

        # Remove anything in Unicode "Other" category:
        # Cc (control), Cf (format), Cs (surrogate),
        # Co (private use), Cn (unassigned)
        if category.startswith("C"):
            continue

        cleaned.append(ch)

    return "".join(cleaned)


def clean_extracted_text(text: str) -> str:
    """
    Full cleaning pipeline for PDF-extracted text
    safe for RAG + RAGAS transforms.
    """
    if not text:
        return ""

    # Normalize unicode compatibility characters
    text = unicodedata.normalize("NFKC", text)

    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove ASCII control characters (JSON-breaking range)
    text = DISALLOWED_ASCII_CONTROLS.sub("", text)

    # Remove Unicode control/format characters
    text = strip_unicode_controls(text)

    # Normalize whitespace
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


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
    # text = extract_plain_text(path)
    # text = clean_extracted_text(text)
    # return [Document(page_content=text, metadata={"source": str(path)})]
    markdown = pymupdf4llm.to_markdown(path)
    # markdown = clean_extracted_text(markdown)
    markdown = clean_extracted_text(markdown)
    print("disallowed ASCII controls:", count_disallowed_ascii_controls(markdown))
    print("unicode controls:", count_unicode_controls(markdown))
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

def count_control_chars(s: str) -> int:
    return len(re.findall(r"[\x00-\x1F\x7F]", s or ""))


# DISALLOWED_ASCII_CONTROLS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
# ALLOWED = {"\n", "\r", "\t"}

def count_disallowed_ascii_controls(s: str) -> int:
    return len(DISALLOWED_ASCII_CONTROLS.findall(s or ""))

def count_unicode_controls(s: str) -> int:
    n = 0
    for ch in (s or ""):
        if ch in ALLOWED_WHITESPACE:
            continue
        if unicodedata.category(ch).startswith("C"):
            n += 1
    return n


# def strip_unicode_controls(s: str) -> str:
#     out = []
#     for ch in (s or ""):
#         if ch in ALLOWED:
#             out.append(ch)
#             continue
#         cat = unicodedata.category(ch)
#         # Remove all "Other" categories:
#         # Cc control, Cf format, Cs surrogate, Co private use, Cn unassigned
#         if cat.startswith("C"):
#             continue
#         out.append(ch)
#     return "".join(out)

# def clean_extracted_text_strict(text: str) -> str:
#     if not text:
#         return ""
#     text = unicodedata.normalize("NFKC", text)
#     text = text.replace("\r\n", "\n").replace("\r", "\n")
#     text = DISALLOWED_ASCII_CONTROLS.sub("", text)  # already working for you
#     text = strip_unicode_controls(text)             # ✅ removes Cf/Cc/etc.
#     # optional whitespace normalization
#     text = re.sub(r"[ \t]{2,}", " ", text)
#     text = re.sub(r"\n{3,}", "\n\n", text)
#     return text.strip()


if __name__ == "__main__":
    docs = extract_playbooks(
        # urls=[
        #     "https://docs.lumu.io/portal/en/kb/articles/network-scan-response-playbook",
        #     "https://docs.lumu.io/portal/en/kb/articles/network-bruteforce-ir-playbook",
        # ],
        pdf_paths=[
            # "data/kb/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf",
            # "data/kb/NIST.SP.800-61r2.pdf",
            "data/kb/network-scan-response-playbook.pdf",
            "data/kb/network-bruteforce-ir-playbook.pdf",
        ],
    )
    output_path = "data/playbooks4.json"
    save_documents(docs, output_path)
    print(f"Saved {len(docs)} documents to {output_path}")

    docs = load_documents("data/playbooks4.json")
    for doc in docs:
        print(count_control_chars(doc.page_content))
