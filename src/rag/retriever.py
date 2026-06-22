import numpy as np
import chromadb

from pathlib import Path
from sentence_transformers import CrossEncoder
from src.rag.embeddings import EmbeddingModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"
COLLECTION_NAME = "agroclimate_knowledge_base"


class Retriever:

    def __init__(self):

        self.embedding_model = EmbeddingModel()

        self.reranker = CrossEncoder("BAAI/bge-reranker-base")

        self.client = chromadb.PersistentClient(
            path=str(VECTORSTORE_DIR)
        )

        self.collection = self.client.get_collection(
            COLLECTION_NAME
        )

    def _cosine(self, a, b):
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _mmr(self, query_vec, docs, doc_vecs, k=5, lambda_param=0.5):

        selected = []
        selected_idx = []

        doc_scores = [
            self._cosine(query_vec, v) for v in doc_vecs
        ]

        candidates = list(range(len(docs)))

        while len(selected) < k and candidates:

            mmr_scores = []

            for i in candidates:

                sim_to_query = doc_scores[i]

                if not selected_idx:
                    diversity_penalty = 0
                else:
                    diversity_penalty = max(
                        self._cosine(doc_vecs[i], doc_vecs[j])
                        for j in selected_idx
                    )

                mmr_score = (
                    lambda_param * sim_to_query
                    - (1 - lambda_param) * diversity_penalty
                )

                mmr_scores.append((mmr_score, i))

            _, best_idx = max(mmr_scores)

            selected.append(docs[best_idx])
            selected_idx.append(best_idx)
            candidates.remove(best_idx)

        return selected

    def _rerank(self, query, docs):

        pairs = [(query, doc) for doc in docs]

        scores = self.reranker.predict(pairs)

        scored_docs = list(zip(scores, docs))

        scored_docs.sort(reverse=True, key=lambda x: x[0])

        return [doc for _, doc in scored_docs]

    def search(self, query, top_k=5, category=None):

        query_vec = self.embedding_model.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=20,  # importante para reranker funcionar bem
            where={"category": category} if category else None,
            include=["documents", "embeddings", "metadatas"]
        )

        docs = results["documents"][0]
        doc_vecs = results["embeddings"][0]
        metadatas = results["metadatas"][0]

        mmr_docs = self._mmr(
            query_vec,
            docs,
            doc_vecs,
            k=min(10, len(docs))
        )

        final_docs = self._rerank(query, mmr_docs)

        return {
            "documents": [final_docs[:top_k]],
            "metadatas": [metadatas[:len(final_docs[:top_k])]]
        }