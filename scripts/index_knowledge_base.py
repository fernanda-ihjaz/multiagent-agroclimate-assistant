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


def index_knowledge_base():

    documents = load_pdf_documents(str(DOCS_DIR))

    chunks = chunk_documents(documents)

    embedding_model = EmbeddingModel()

    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    ids = [
        f"{meta['filename']}_p{meta['page']}_c{meta['chunk_id']}"
        for meta in metadatas
    ]

    embeddings = embedding_model.embed_texts(texts)

    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(VECTORSTORE_DIR)
    )

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME
    )

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"base salva em: {VECTORSTORE_DIR}")


if __name__ == "__main__":
    index_knowledge_base()