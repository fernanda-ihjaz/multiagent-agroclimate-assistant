import json
import re
from datetime import datetime

from src.llm.ollama_client import OllamaClient

_CURRENT_YEAR = datetime.today().year
_CURRENT_DATE = datetime.today().strftime("%Y-%m-%d")

SYSTEM_PROMPT = f"""
Você é um analisador de intenção para um assistente agroclimático.

Data atual: {_CURRENT_DATE}

Extraia as informações da pergunta do usuário e retorne APENAS um JSON válido, sem texto adicional, sem markdown, sem blocos de código.

Campos obrigatórios:
- "cultura": "soja" ou "trigo" (inferir da pergunta; padrão "trigo")
- "data_inicio": "YYYY-MM-DD" do período principal de análise
- "data_fim": "YYYY-MM-DD" do período principal de análise
- "doenca": nome da doença mencionada ou null
- "tem_comparacao": true se o usuário quer comparar com outro período, false caso contrário
- "data_inicio_comparacao": "YYYY-MM-DD" ou null (período de comparação, se houver)
- "data_fim_comparacao": "YYYY-MM-DD" ou null

Regras para inferência de datas:
- "março de 2025" → data_inicio: "2025-03-01", data_fim: "2025-03-31"
- "junho de 2024" → data_inicio: "2024-06-01", data_fim: "2024-06-30"
- "2025" sem mês → data_inicio: "2025-01-01", data_fim: "2025-12-31"
- Se o usuário perguntar se pode "se repetir em 2026" ou "comparar com 2026", isso é tem_comparacao: true
- Para "pode se repetir em 2026": use o mesmo mês do período principal mas no ano mencionado

Retorne apenas o JSON. Exemplo:
{{"cultura":"soja","data_inicio":"2025-03-01","data_fim":"2025-03-31","doenca":"giberela","tem_comparacao":true,"data_inicio_comparacao":"2026-03-01","data_fim_comparacao":"2026-03-31"}}
"""


class IntentAgent:

    def __init__(self):
        self.llm = OllamaClient()

    def run(self, question: str) -> dict:
        raw = self.llm.generate(f"{SYSTEM_PROMPT}\n\nPergunta: {question}\n\nJSON:")

        cleaned = self._clean_json(raw)

        try:
            intent = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            intent = {}

        return self._apply_defaults(intent)

    def _clean_json(self, text: str) -> str:
        text = text.strip()

        block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if block:
            return block.group(1).strip()

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return match.group(0)

        return text

    def _apply_defaults(self, intent: dict) -> dict:
        today = datetime.today()

        defaults = {
            "cultura": "trigo",
            "data_inicio": (today.replace(day=1)).strftime("%Y-%m-%d"),
            "data_fim": today.strftime("%Y-%m-%d"),
            "doenca": None,
            "tem_comparacao": False,
            "data_inicio_comparacao": None,
            "data_fim_comparacao": None,
        }

        for key, value in defaults.items():
            if key not in intent or intent[key] is None and key in ("cultura", "data_inicio", "data_fim"):
                intent[key] = value

        if intent.get("cultura") not in ("soja", "trigo"):
            intent["cultura"] = "trigo"

        return intent