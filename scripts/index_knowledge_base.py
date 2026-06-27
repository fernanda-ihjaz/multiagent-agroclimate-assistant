import re
import sys
from pathlib import Path

import chromadb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.rag.loader import load_pdf_documents, chunk_documents
from src.rag.embeddings import EmbeddingModel


DOCS_DIR = PROJECT_ROOT / "data" / "docs"
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"
COLLECTION_NAME = "agroclimate_knowledge_base"

UPSERT_BATCH_SIZE = 100


def safe_id(text):
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", text)


def index_knowledge_base():
    print("Carregando PDFs...")
    documents = load_pdf_documents(str(DOCS_DIR))

    print("Fazendo chunking...")
    chunks = chunk_documents(documents)

    if not chunks:
        raise ValueError("Nenhum chunk foi gerado. Verifique os PDFs em data/docs")

    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [
        safe_id(f"{meta['filename']}_p{meta['page']}_c{meta['chunk_id']}")
        for meta in metadatas
    ]

    print(f"Total de chunks: {len(chunks)}. Gerando embeddings em lotes...")

    embedding_model = EmbeddingModel()
    embeddings = embedding_model.embed_texts(texts, batch_size=16)

    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))

    existing_names = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing_names:
        print("Coleção existente encontrada. Removendo...")
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(name=COLLECTION_NAME)

    print(f"Salvando no vectorstore em lotes de {UPSERT_BATCH_SIZE}...")

    total = len(chunks)
    for start in range(0, total, UPSERT_BATCH_SIZE):
        end = min(start + UPSERT_BATCH_SIZE, total)
        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end]
        )
        print(f"  [{end}/{total}] chunks salvos")

    print(f"\nBase salva em: {VECTORSTORE_DIR}")
    print(f"Total de chunks indexados: {total}")


if __name__ == "__main__":
    index_knowledge_base()