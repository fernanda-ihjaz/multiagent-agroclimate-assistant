from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingModel:

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5"
    ):

        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts):

        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            normalize_embeddings=True 
        )

        return embeddings.tolist()

    def embed_query(self, query: str):

        enhanced_query = f"climate agricultural risk: {query}"

        embedding = self.model.encode(
            enhanced_query,
            normalize_embeddings=True
        )

        return embedding.tolist()