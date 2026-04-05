from langchain_community.document_loaders import TextLoader

def loadDoc():
    loader = TextLoader('manim_docs.md', encoding='utf-8')
    docs = loader.load()
    print(docs[0])
    
loadDoc()

