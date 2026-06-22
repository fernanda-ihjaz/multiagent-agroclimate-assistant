from pathlib import Path
from pypdf import PdfReader


def load_pdf_documents(docs_dir: str = "data/docs"):
    #carrega arquivos PDF da pasta docs e extrai o texto página por página
    #retorna uma lista de documentos com metadados

    docs_path = Path(docs_dir)
    documents = []

    if not docs_path.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {docs_dir}")

    pdf_files = list(docs_path.rglob("*.pdf"))  # procura em todas as subpastas

    if not pdf_files:
        raise FileNotFoundError(f"Nenhum PDF encontrado em: {docs_dir}")

    for pdf_file in pdf_files:
        reader = PdfReader(str(pdf_file))

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            if text and text.strip():
                documents.append({
                    "text": text.strip(),
                    "metadata": {
                        "source": str(pdf_file),
                        "filename": pdf_file.name,
                        "category": pdf_file.parent.name,
                        "page": page_number,
                    },
                })

    return documents


def chunk_documents(documents, chunk_size: int = 250, chunk_overlap: int = 50):

    chunks = []

    for doc in documents:
        text = doc["text"]
        metadata = doc["metadata"]

        #separa por palavras
        words = text.split()

        start = 0
        chunk_id = 0

        while start < len(words):

            end = start + chunk_size
            chunk_words = words[start:end]

            chunk_text = " ".join(chunk_words).strip()

            #evita chunks vazios ou inúteis
            if len(chunk_text) > 30:

                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        **metadata,
                        "chunk_id": chunk_id,
                    },
                })

                chunk_id += 1

            #move janela com overlap
            start += chunk_size - chunk_overlap

    return chunks