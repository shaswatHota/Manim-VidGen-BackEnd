from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import re

def loadnSplitDoc():
    # 1. Load raw text
    loader = TextLoader('manim_docs.md', encoding='utf-8')
    raw_docs = loader.load()
    content = raw_docs[0].page_content

    # 2. PRE-PROCESS: Remove those "=====" lines that confuse splitters
    # This turns the "Quickstart ====" into a clean "Quickstart"
    clean_content = re.sub(r'={3,}', '', content)

    # 3. STAGE 1: Split by Markdown structure
    # We use RecursiveCharacterTextSplitter with MD headers to keep sections together
    md_splitter = RecursiveCharacterTextSplitter(
        separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n"],
        chunk_size=1500,
        chunk_overlap=200
    )
    md_docs = md_splitter.create_documents([clean_content])

    # 4. STAGE 2: Atomic Code Splitting
    # We loop through our MD chunks and if they contain code, 
    # we ensure they follow Python logic rules.
    python_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=800, 
        chunk_overlap=50
    )

    final_chunks = []
    for doc in md_docs:
        # If the chunk has a code block, split it with Python awareness
        if "```python" in doc.page_content:
            python_sub_chunks = python_splitter.split_documents([doc])
            final_chunks.extend(python_sub_chunks)
        else:
            final_chunks.append(doc)

    # Result
    # print(f"Total Atomic Chunks: {len(final_chunks)}")
    # print("--- Sample Chunk ---")
    # print(final_chunks[3].page_content) 

loadnSplitDoc()