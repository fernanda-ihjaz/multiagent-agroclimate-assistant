from sentence_transformers import SentenceTransformer


class EmbeddingModel:

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3" #melhores respostas em portugues
    ):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts):
        #gera embeddings normalizados para uma lista de textos.
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        return embeddings.tolist()

    def embed_query(self, query: str):

        #gera embedding normalizado para uma pergunta do usuário.
        enhanced_query = (
            "risco agroclimático agricultura clima lavoura trigo soja "
            f"Passo Fundo RS: {query}"
        )

        embedding = self.model.encode(
            enhanced_query,
            normalize_embeddings=True
        )

        return embedding.tolist()