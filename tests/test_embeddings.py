from src.rag.embeddings import EmbeddingModel

model = EmbeddingModel()

embedding = model.embed_query(
    "Qual o melhor período para plantar soja no Rio Grande do Sul?"
)

print(type(embedding))
print(len(embedding))
print(embedding[:10])