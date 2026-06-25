from src.llm.ollama_client import OllamaClient


SYSTEM_PROMPT = """
Você é um especialista agrícola.

Responda usando apenas o contexto fornecido.
Não invente informações.
Não utilize conhecimento externo se ele não estiver presente no contexto.

Quando usar uma informação do contexto, preserve as citações no formato:
[arquivo, página X]

Se a informação não estiver presente no contexto, diga:
"Não encontrei dados suficientes na base documental para responder com segurança."

A resposta deve ser:
- técnica;
- objetiva;
- clara;
- útil para apoio à decisão agroclimática;
- focada em trigo, soja e região Sul/RS quando aplicável.
"""


class RAGAgent:
    #agente responsável por responder perguntas com base no contexto recuperado pelo RAG
    def __init__(self):
        self.llm = OllamaClient()

    def run(
        self,
        question,
        context
    ):
        prompt = f"""
{SYSTEM_PROMPT}

Contexto disponível:

{context}

Pergunta do usuário:

{question}

Resposta:
"""

        return self.llm.generate(prompt)