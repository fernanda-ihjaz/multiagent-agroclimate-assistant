from src.rag.retriever import Retriever

retriever = Retriever()

results = retriever.search(
    query="ferrugem asiática",
    top_k=3,
    category="soy"
)

for doc in results["documents"][0]:
    print(doc[:500])