from pathlib import Path

import chromadb
import numpy as np

from src.rag.embeddings import EmbeddingModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"
COLLECTION_NAME = "agroclimate_knowledge_base"

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Retriever:

    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self._reranker = None

        self.client = chromadb.PersistentClient(
            path=str(VECTORSTORE_DIR)
        )

        self.collection = self.client.get_collection(
            COLLECTION_NAME
        )

    @property
    def reranker(self):
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(
                RERANKER_MODEL,
                max_length=512
            )
        return self._reranker

    def _cosine(self, a, b):
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a, b) / (norm_a * norm_b))

    def _mmr(self, query_vec, items, k=5, lambda_param=0.5):
        if not items:
            return []

        selected = []
        selected_idx = []
        doc_vecs = [item["embedding"] for item in items]
        doc_scores = [self._cosine(query_vec, vec) for vec in doc_vecs]
        candidates = list(range(len(items)))

        while len(selected) < k and candidates:
            mmr_scores = []

            for i in candidates:
                sim_to_query = doc_scores[i]

                diversity_penalty = (
                    max(
                        self._cosine(doc_vecs[i], doc_vecs[j])
                        for j in selected_idx
                    )
                    if selected_idx
                    else 0.0
                )

                mmr_score = (
                    lambda_param * sim_to_query
                    - (1 - lambda_param) * diversity_penalty
                )
                mmr_scores.append((mmr_score, i))

            _, best_idx = max(mmr_scores, key=lambda x: x[0])
            selected.append(items[best_idx])
            selected_idx.append(best_idx)
            candidates.remove(best_idx)

        return selected

    def _rerank(self, query, items):
        if not items:
            return []

        try:
            pairs = [(query, item["document"][:512]) for item in items]
            scores = self.reranker.predict(pairs, batch_size=4)

            scored = sorted(zip(scores, items), reverse=True, key=lambda x: x[0])

            return [
                {**item, "rerank_score": float(score)}
                for score, item in scored
            ]

        except (MemoryError, OSError):
            query_vec = self.embedding_model.embed_query(query)
            scored = sorted(
                items,
                reverse=True,
                key=lambda item: self._cosine(query_vec, item["embedding"])
            )
            return [
                {**item, "rerank_score": self._cosine(query_vec, item["embedding"])}
                for item in scored
            ]

    def search(self, query, top_k=5, category=None):
        query_vec = self.embedding_model.embed_query(query)

        where_filter = {"category": category} if category else None

        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=min(20, self.collection.count()),
            where=where_filter,
            include=["documents", "embeddings", "metadatas"]
        )

        docs = results.get("documents", [[]])[0]
        doc_vecs = results.get("embeddings", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not docs:
            return {"documents": [[]], "metadatas": [[]]}

        items = [
            {"document": doc, "metadata": meta, "embedding": emb}
            for doc, meta, emb in zip(docs, metadatas, doc_vecs)
        ]

        mmr_items = self._mmr(
            query_vec=query_vec,
            items=items,
            k=min(10, len(items)),
            lambda_param=0.5
        )

        reranked_items = self._rerank(query=query, items=mmr_items)
        final_items = reranked_items[:top_k]

        return {
            "documents": [[item["document"] for item in final_items]],
            "metadatas": [
                [
                    {**item["metadata"], "rerank_score": item.get("rerank_score")}
                    for item in final_items
                ]
            ]
        }