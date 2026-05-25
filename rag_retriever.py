"""FAISS vector store + similarity retriever over chunked Manim docs."""

from __future__ import annotations

import json
import os
import voyageai
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from docLoader import loadnSplitDoc

if TYPE_CHECKING:
    from langchain_core.runnables import Runnable

ROOT = Path(__file__).resolve().parent
VECTOR_DIR = ROOT / "vectorstore_faiss"
MANIFEST = VECTOR_DIR / "source_manifest.json"
EMBED_MODEL = "models/text-embedding-004"

_manim_retriever: Optional[Runnable] = None


def _source_mtime_ns(md_path: Path) -> int:
    return md_path.stat().st_mtime_ns


def _manifest_matches(md_path: Path) -> bool:
    if not MANIFEST.is_file():
        return False
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return int(data.get("mtime", -1)) == _source_mtime_ns(md_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return False


def _write_manifest(md_path: Path) -> None:
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps({"mtime": _source_mtime_ns(md_path)}),
        encoding="utf-8",
    )


def _embeddings() -> GoogleGenerativeAIEmbeddings:
    key = os.environ.get("GEMINI_API_KEY")

    if not key:
        raise ValueError("GEMINI_API_KEY required for embeddings")
    return GoogleGenerativeAIEmbeddings(
        model=EMBED_MODEL,
        google_api_key=key,
    )


def build_or_load_retriever(
    md_path: Path | None = None,
    k: int = 6,
) -> Runnable:
    """Similarity search retriever over Manim docs; rebuilds FAISS if source changed."""
    md = Path(md_path) if md_path else ROOT / "manim_docs.md"
    if not md.is_file():
        raise FileNotFoundError(f"Manim docs not found: {md}")

    emb = _embeddings()
    print("Embeddings initialized")

    index_faiss = VECTOR_DIR / "index.faiss"
    if index_faiss.is_file() and _manifest_matches(md):
        vs = FAISS.load_local(
            str(VECTOR_DIR),
            emb,
            allow_dangerous_deserialization=True,
        )
    else:
        chunks = loadnSplitDoc(str(md))
        print("chunks loaded , length of the doc is ",len(chunks))
        if not chunks:
            raise ValueError("No document chunks produced from manim_docs")
        vs = FAISS.from_documents(chunks, emb)
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        vs.save_local(str(VECTOR_DIR))
        _write_manifest(md)

    return vs.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


def init_manim_rag(k: int = 6) -> Optional[Runnable]:
    """Build retriever at startup; returns None if docs or embedding setup fails."""
    global _manim_retriever
    try:
        _manim_retriever = build_or_load_retriever(k=k)
    except Exception as e:
        print(f"[RAG] Manim retriever not available: {e}")
        _manim_retriever = None
    return _manim_retriever


def retrieve_context(query: str) -> str:
    """Run similarity search and concatenate chunk text for LLM injection."""
    if _manim_retriever is None or not query.strip():
        return ""
    docs = _manim_retriever.invoke(query)
    parts = [d.page_content for d in docs if getattr(d, "page_content", None)]
    print("\n------------------------------------------\n",parts)
    
    return "\n\n---\n\n".join(parts)
