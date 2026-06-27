from ollama import embed

class EmbeddingModel:

    def __init__(self, model_name: str = "nomic-embed-text"):
        self.model_name = model_name

    def embed_texts(self, texts: list, batch_size: int = 16) -> list:
        """
        Gera embeddings para uma lista de textos em lotes.
        Mantém a mesma interface da implementação anterior.
        """
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = embed(
                model=self.model_name,
                input=batch
            )

            all_embeddings.extend(response["embeddings"])

        return all_embeddings

    def embed_query(self, query: str) -> list:
        """
        Gera embedding para uma consulta.
        """

        enhanced_query = (
            "risco agroclimático agricultura clima lavoura trigo soja "
            f"Passo Fundo RS: {query}"
        )

        response = embed(
            model=self.model_name,
            input=enhanced_query
        )

        return response["embeddings"][0]