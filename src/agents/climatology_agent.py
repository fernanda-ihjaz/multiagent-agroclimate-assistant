import asyncio
import json
import sys
from pathlib import Path

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession

from src.llm.ollama_client import OllamaClient

SERVER_SCRIPT = Path(__file__).resolve().parents[1] / "mcp_servers" / "climate_server.py"

SYSTEM_PROMPT = """
Você é um especialista em climatologia agrícola.

Interprete os índices agroclimáticos fornecidos e responda à pergunta.

Seja objetivo e técnico. Baseie-se exclusivamente nos dados fornecidos.
Se um índice for nulo, informe que o dado não está disponível.
Não invente valores ou interpretações sem respaldo nos números.
"""


class ClimatologyAgent:

    def __init__(self):
        self.llm = OllamaClient()

    def run(
        self,
        question: str,
        cultura: str,
        data_inicio: str,
        data_fim: str,
        estacao: str = "PASSO FUNDO"
    ) -> dict:
        return asyncio.run(
            self._run_async(question, cultura, data_inicio, data_fim, estacao)
        )

    async def _run_async(
        self,
        question: str,
        cultura: str,
        data_inicio: str,
        data_fim: str,
        estacao: str
    ) -> dict:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_SCRIPT)]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                weather_result = await session.call_tool(
                    "fetch_weather_tool",
                    {
                        "data_inicio": data_inicio,
                        "data_fim": data_fim,
                        "estacao": estacao
                    }
                )

                serie_json = weather_result.content[0].text

                try:
                    probe = json.loads(serie_json)
                    if isinstance(probe, dict) and "error" in probe:
                        return {
                            "indices": {},
                            "interpretation": f"Erro ao buscar dados climáticos: {probe['error']}"
                        }
                    if isinstance(probe, list) and len(probe) == 0:
                        return {
                            "indices": {},
                            "interpretation": "Nenhum dado climático encontrado para o período e estação informados."
                        }
                except json.JSONDecodeError:
                    pass

                indices_result = await session.call_tool(
                    "calculate_indices_tool",
                    {
                        "serie_json": serie_json,
                        "cultura": cultura
                    }
                )

                indices_json = indices_result.content[0].text
                indices = json.loads(indices_json)

                if "error" in indices:
                    return {
                        "indices": {},
                        "interpretation": f"Não foi possível calcular os índices: {indices['error']}"
                    }

                interpretation = self.llm.generate(
                    self._build_prompt(question, indices)
                )

                return {
                    "indices": indices,
                    "interpretation": interpretation
                }

    def _build_prompt(self, question: str, indices: dict) -> str:
        return f"""
{SYSTEM_PROMPT}

Índices agroclimáticos calculados:
{json.dumps(indices, indent=2, ensure_ascii=False)}

Pergunta do usuário:
{question}

Análise climatológica:
"""