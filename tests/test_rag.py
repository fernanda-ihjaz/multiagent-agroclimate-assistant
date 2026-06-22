from src.rag.retriever import Retriever


retriever = Retriever()

query = "qual o risco de geada no trigo?"

results = retriever.search(
    query=query,
    top_k=3
)

print("\nPERGUNTA:")
print(query)

print("\nRESULTADOS:\n")

for i, doc in enumerate(results["documents"][0], start=1):

    print("=" * 80)

    print(f"Resultado {i}")

    print(doc[:500])

    print()