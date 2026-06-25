from src.rag.loader import load_pdf_documents

#teste para o loader

documents = load_pdf_documents()

print(f"Total de documentos carregados: {len(documents)}")

if documents:
    print("\nPrimeiro documento:")
    print(documents[0]["metadata"])
    print("\nTrecho do texto:")
    print(documents[0]["text"][:500])