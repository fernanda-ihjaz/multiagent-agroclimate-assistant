from src.rag.loader import (
    load_pdf_documents,
    chunk_documents
)

documents = load_pdf_documents()

chunks = chunk_documents(documents)

print(f"Documentos: {len(documents)}")
print(f"Chunks: {len(chunks)}")

print(chunks[0]["metadata"])
print(chunks[0]["text"][:300])