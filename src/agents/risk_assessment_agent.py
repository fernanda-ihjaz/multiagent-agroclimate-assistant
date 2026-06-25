from src.llm.ollama_client import OllamaClient


SYSTEM_PROMPT = """
Você é um analista de risco agrícola especializado em trigo e soja no Rio Grande do Sul.

Avalie o cenário considerando:
- risco de geada;
- risco hídrico;
- risco térmico;
- risco fitossanitário;
- risco de doenças;
- evidências documentais e climáticas disponíveis.

Não invente dados.
Se houver incerteza, declare a incerteza.

Responda obrigatoriamente no formato:

Nível de risco:
baixo / moderado / alto / inconclusivo

Justificativa:
explique tecnicamente o motivo da avaliação.

Fatores agravantes:
liste os fatores que aumentam o risco.

Fatores de mitigação:
liste os fatores que reduzem ou controlam o risco.

Incertezas:
explique quais dados faltam para uma avaliação mais segura.

Recomendação técnica:
apresente uma recomendação objetiva e prudente.
"""


class RiskAssessmentAgent:
    #agente responsável pela avaliação de risco agroclimático e fitossanitário
    def __init__(self):
        self.llm = OllamaClient()

    def run(self, scenario):
        prompt = f"""
{SYSTEM_PROMPT}

Cenário para avaliação:

{scenario}

Avaliação:
"""

        return self.llm.generate(prompt)