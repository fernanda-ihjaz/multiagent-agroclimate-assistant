from src.llm.ollama_client import OllamaClient


SYSTEM_PROMPT = """
Você é um revisor técnico agrícola.

Revise a resposta recebida melhorando:
- clareza;
- precisão;
- consistência;
- organização;
- linguagem técnica.

Regras obrigatórias:
- não adicione fatos novos;
- não invente recomendações;
- não remova citações;
- não altere nomes de arquivos citados;
- não altere números de páginas citados;
- preserve incertezas declaradas;
- preserve alertas de falta de dados.

Retorne apenas a versão revisada da resposta.
"""


class ReviewAgent:
    #agente responsável por revisar a resposta final
    def __init__(self):
        self.llm = OllamaClient()

    def run(self, answer):
        prompt = f"""
{SYSTEM_PROMPT}

Resposta a revisar:

{answer}

Versão revisada:
"""

        return self.llm.generate(prompt)