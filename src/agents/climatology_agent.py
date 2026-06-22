from src.llm.ollama_client import OllamaClient


SYSTEM_PROMPT = """
Você é um especialista em climatologia agrícola.

Responda perguntas sobre:
- clima
- temperatura
- precipitação
- geadas
- seca
- condições meteorológicas

Forneça respostas objetivas e técnicas.
"""


class ClimatologyAgent:

    def __init__(self):

        self.llm = OllamaClient()

    def run(self, question):

        prompt = f"""
{SYSTEM_PROMPT}

Pergunta:
{question}
"""

        return self.llm.generate(prompt)