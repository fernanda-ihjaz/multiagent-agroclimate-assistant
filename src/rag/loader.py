from pathlib import Path

from pypdf import PdfReader


def load_pdf_documents(docs_dir: str = "data/docs"):

    #carrega arquivos PDF da pasta docs e extrai o texto página por página.
    #retorna uma lista de documentos com metadados:


    docs_path = Path(docs_dir)
    documents = []

    if not docs_path.exists():
        raise FileNotFoundError(
            f"Diretório não encontrado: {docs_dir}"
        )

    pdf_files = list(
        docs_path.rglob("*.pdf")
    )

    if not pdf_files:
        raise FileNotFoundError(
            f"Nenhum PDF encontrado em: {docs_dir}"
        )

    for pdf_file in pdf_files:
        try:
            reader = PdfReader(
                str(pdf_file)
            )
        except Exception as error:
            print(
                f"Erro ao abrir PDF {pdf_file}: {error}"
            )
            continue

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):
            try:
                text = page.extract_text()
            except Exception as error:
                print(
                    f"Erro ao extrair página {page_number} de {pdf_file}: {error}"
                )
                continue

            if text and text.strip():
                try:
                    source = str(
                        pdf_file.relative_to(docs_path)
                    )
                except ValueError:
                    source = str(pdf_file)

                documents.append(
                    {
                        "text": text.strip(),
                        "metadata": {
                            "source": source,
                            "filename": pdf_file.name,
                            "category": pdf_file.parent.name,
                            "page": page_number
                        }
                    }
                )

    return documents


def chunk_documents(
    documents,
    chunk_size: int = 250,
    chunk_overlap: int = 50
):

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap precisa ser menor que chunk_size."
        )

    chunks = []

    for doc in documents:
        text = doc["text"]
        metadata = doc["metadata"]

        words = text.split()

        start = 0
        chunk_id = 0

        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]

            chunk_text = " ".join(
                chunk_words
            ).strip()

            if len(chunk_text) > 30:
                chunks.append(
                    {
                        "text": chunk_text,
                        "metadata": {
                            **metadata,
                            "chunk_id": chunk_id,
                            "word_count": len(chunk_words),
                            "char_count": len(chunk_text)
                        }
                    }
                )

                chunk_id += 1

            start += chunk_size - chunk_overlap

    return chunks
