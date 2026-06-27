import json
from src.llm.ollama_client import OllamaClient

SYSTEM_PROMPT = """
Você é um especialista agroclimático sintetizando uma análise técnica para um produtor rural.

Você recebe um conjunto estruturado de informações (índices, análises e avaliação de risco) e deve produzir UMA resposta coesa, clara e direta — não uma colagem de seções.

Regras obrigatórias:
- Responda diretamente à pergunta do usuário no primeiro parágrafo.
- Integre os dados climáticos, o conhecimento documental e o risco em uma narrativa fluida.
- Não use cabeçalhos como "Análise climatológica:", "Base documental:", "Avaliação de risco:".
- Se houver dois períodos (comparação), compare-os de forma natural no texto.
- Mantenha citações documentais no formato [arquivo, página X] onde relevante.
- Não invente dados. Se algo estiver ausente, mencione brevemente e siga.
- Tom técnico, mas legível. Sem jargão desnecessário.
- Máximo de 4 parágrafos.
"""


class ReviewAgent:

    def __init__(self):
        self.llm = OllamaClient()

    def run(self, synthesis: dict, question: str) -> str:
        synthesis_text = json.dumps(synthesis, indent=2, ensure_ascii=False)

        prompt = f"""
{SYSTEM_PROMPT}

Pergunta original do usuário:
{question}

Dados sintetizados:
{synthesis_text}

Resposta integrada:
"""
        return self.llm.generate(prompt)