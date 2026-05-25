import re
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter


def loadnSplitDoc(md_path: str | None = None) -> list:
    """Load Manim markdown docs and return LangChain Document chunks."""
    base = Path(__file__).resolve().parent
    path = Path(md_path) if md_path else base / "manim_docs.md"

    loader = TextLoader(str(path), encoding="utf-8")
    raw_docs = loader.load()
    content = raw_docs[0].page_content

    clean_content = re.sub(r"={3,}", "", content)

    md_splitter = RecursiveCharacterTextSplitter(
        separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n"],
        chunk_size=1500,
        chunk_overlap=200,
    )
    md_docs = md_splitter.create_documents([clean_content])

    python_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=800,
        chunk_overlap=50,
    )

    final_chunks = []
    for doc in md_docs:
        if "```python" in doc.page_content:
            python_sub_chunks = python_splitter.split_documents([doc])
            final_chunks.extend(python_sub_chunks)
        else:
            final_chunks.append(doc)

    return final_chunks
