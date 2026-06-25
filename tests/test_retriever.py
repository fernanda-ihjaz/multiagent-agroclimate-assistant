from src.rag.retriever import Retriever


def test_retriever_returns_documents_and_metadatas():
    retriever = Retriever()

    result = retriever.search(
        query="Quais condições favorecem giberela no trigo?",
        top_k=3,
        category="wheat"
    )

    assert "documents" in result
    assert "metadatas" in result

    documents = result["documents"][0]
    metadatas = result["metadatas"][0]

    assert isinstance(documents, list)
    assert isinstance(metadatas, list)

    assert len(documents) == len(metadatas)

    if documents:
        assert isinstance(documents[0], str)
        assert "filename" in metadatas[0]
        assert "page" in metadatas[0]
        assert "category" in metadatas[0]


def test_retriever_category_filter():
    retriever = Retriever()

    result = retriever.search(
        query="ferrugem asiática da soja",
        top_k=3,
        category="soy"
    )

    metadatas = result["metadatas"][0]

    for metadata in metadatas:
        assert metadata["category"] == "soy"
