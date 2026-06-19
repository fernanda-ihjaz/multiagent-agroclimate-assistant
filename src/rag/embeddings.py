from sentence_transformers import SentenceTransformer


class EmbeddingModel:

    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts):
        #Gera embeddings para uma lista de textos

        return self.model.encode(
            texts,
            show_progress_bar=True
        ).tolist()

    def embed_query(self, query):

        return self.model.encode(
            [query]
        ).tolist()[0]