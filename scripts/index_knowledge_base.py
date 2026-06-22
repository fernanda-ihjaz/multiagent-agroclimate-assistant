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


def safe_id(text):
    #normaliza IDs para evitar problemas com caracteres especiais

    return re.sub(
        r"[^a-zA-Z0-9_\-]",
        "_",
        text
    )


def index_knowledge_base():
    #indexa os PDFs da pasta data/docs no Chroma
    print("Carregando PDFs")
    documents = load_pdf_documents(
        str(DOCS_DIR)
    )

    print("Fazendo chunking")
    chunks = chunk_documents(
        documents
    )

    if not chunks:
        raise ValueError(
            "Nenhum chunk foi gerado. Verifique os PDFs em data/docs"
        )

    embedding_model = EmbeddingModel()

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    metadatas = [
        chunk["metadata"]
        for chunk in chunks
    ]

    ids = [
        safe_id(
            f"{meta['filename']}_p{meta['page']}_c{meta['chunk_id']}"
        )
        for meta in metadatas
    ]

    print("Gerando embeddings")
    embeddings = embedding_model.embed_texts(
        texts
    )

    VECTORSTORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=str(VECTORSTORE_DIR)
    )

    existing_collections = [
        collection.name
        for collection in client.list_collections()
    ]

    if COLLECTION_NAME in existing_collections:
        print("Coleção existente encontrada. Removendo coleção antiga...")
        client.delete_collection(
            COLLECTION_NAME
        )

    collection = client.create_collection(
        name=COLLECTION_NAME
    )

    print("Salvando no vectorstore")
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"Base salva em: {VECTORSTORE_DIR}")
    print(f"Total de chunks indexados: {len(chunks)}")


if __name__ == "__main__":
    index_knowledge_base()