from src.rag.retriever import Retriever

TEST_CASES = [
    {
        "query": "qual o risco de geada no trigo?",
        "expected_keywords": ["geada", "trigo", "temperatura", "frio"]
    },
    {
        "query": "ferrugem asiática na soja",
        "expected_keywords": ["ferrugem", "soja", "Phakopsora", "doença"]
    }
]


retriever = Retriever()
def precision_at_k(retrieved_docs, expected_keywords):

    relevant = 0

    for doc in retrieved_docs:

        if any(keyword.lower() in doc.lower() for keyword in expected_keywords):
            relevant += 1

    return relevant / len(retrieved_docs)

def recall_at_k(retrieved_docs, expected_keywords):

    found_keywords = set()

    for doc in retrieved_docs:
        for keyword in expected_keywords:
            if keyword.lower() in doc.lower():
                found_keywords.add(keyword.lower())

    return len(found_keywords) / len(expected_keywords)

def run_evaluation():

    results_summary = []

    for test in TEST_CASES:

        query = test["query"]
        expected = test["expected_keywords"]

        results = retriever.search(query=query, top_k=5)

        docs = results["documents"][0]

        precision = precision_at_k(docs, expected)
        recall = recall_at_k(docs, expected)

        results_summary.append({
            "query": query,
            "precision@5": round(precision, 3),
            "recall@5": round(recall, 3)
        })

    print("\nResultados da avaliacao do RAG:\n")

    avg_precision = sum(r["precision@5"] for r in results_summary) / len(results_summary)
    avg_recall = sum(r["recall@5"] for r in results_summary) / len(results_summary)

    for r in results_summary:
        print(f"Query: {r['query']}")
        print(f"Precision@5: {r['precision@5']}")
        print(f"Recall@5: {r['recall@5']}")
        print("-" * 40)

    print("\nMedias gerais:")
    print(f"Precision@5: {round(avg_precision, 3)}")
    print(f"Recall@5: {round(avg_recall, 3)}")