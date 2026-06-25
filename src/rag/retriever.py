from pathlib import Path

import chromadb
import numpy as np
from sentence_transformers import CrossEncoder

from src.rag.embeddings import EmbeddingModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"
COLLECTION_NAME = "agroclimate_knowledge_base"


class Retriever:
    #busca vetorial no Chroma
    #filtro opcional por categoria
    #MMR para diversidade
    #reranking com CrossEncoder
    #preservação correta do vínculo documento-metadado

    def __init__(self):
        self.embedding_model = EmbeddingModel()

        self.reranker = CrossEncoder(
            "BAAI/bge-reranker-base"
        )

        self.client = chromadb.PersistentClient(
            path=str(VECTORSTORE_DIR)
        )

        self.collection = self.client.get_collection(
            COLLECTION_NAME
        )

    def _cosine(self, a, b):
        #calcula similaridade de cosseno entre dois vetores
        a = np.array(a)
        b = np.array(b)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a, b) / (norm_a * norm_b))

    def _mmr(
        self,
        query_vec,
        items,
        k=5,
        lambda_param=0.5
    ):

        selected = []
        selected_idx = []

        if not items:
            return selected

        doc_vecs = [
            item["embedding"] for item in items
        ]

        doc_scores = [
            self._cosine(query_vec, vec)
            for vec in doc_vecs
        ]

        candidates = list(range(len(items)))

        while len(selected) < k and candidates:
            mmr_scores = []

            for i in candidates:
                sim_to_query = doc_scores[i]

                if not selected_idx:
                    diversity_penalty = 0.0
                else:
                    diversity_penalty = max(
                        self._cosine(doc_vecs[i], doc_vecs[j])
                        for j in selected_idx
                    )

                mmr_score = (
                    lambda_param * sim_to_query
                    - (1 - lambda_param) * diversity_penalty
                )

                mmr_scores.append(
                    (mmr_score, i)
                )

            _, best_idx = max(
                mmr_scores,
                key=lambda x: x[0]
            )

            selected.append(items[best_idx])
            selected_idx.append(best_idx)
            candidates.remove(best_idx)

        return selected

    def _rerank(self, query, items):

        #reordena os documentos usando CrossEncoder
        if not items:
            return []

        pairs = [
            (query, item["document"])
            for item in items
        ]

        scores = self.reranker.predict(pairs)

        scored_items = list(
            zip(scores, items)
        )

        scored_items.sort(
            reverse=True,
            key=lambda x: x[0]
        )

        reranked_items = []

        for score, item in scored_items:
            item = {
                **item,
                "rerank_score": float(score)
            }
            reranked_items.append(item)

        return reranked_items

    def search(
        self,
        query,
        top_k=5,
        category=None
    ):
        #busca documentos relevantes na base vetorial
        query_vec = self.embedding_model.embed_query(query)

        where_filter = (
            {"category": category}
            if category
            else None
        )

        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=20,
            where=where_filter,
            include=[
                "documents",
                "embeddings",
                "metadatas"
            ]
        )

        docs = results.get("documents", [[]])[0]
        doc_vecs = results.get("embeddings", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not docs:
            return {
                "documents": [[]],
                "metadatas": [[]]
            }

        items = []

        for doc, metadata, embedding in zip(
            docs,
            metadatas,
            doc_vecs
        ):
            items.append(
                {
                    "document": doc,
                    "metadata": metadata,
                    "embedding": embedding
                }
            )

        mmr_items = self._mmr(
            query_vec=query_vec,
            items=items,
            k=min(10, len(items)),
            lambda_param=0.5
        )

        reranked_items = self._rerank(
            query=query,
            items=mmr_items
        )

        final_items = reranked_items[:top_k]

        documents = [
            item["document"]
            for item in final_items
        ]

        metadatas = [
            {
                **item["metadata"],
                "rerank_score": item.get("rerank_score")
            }
            for item in final_items
        ]

        return {
            "documents": [documents],
            "metadatas": [metadatas]
        }