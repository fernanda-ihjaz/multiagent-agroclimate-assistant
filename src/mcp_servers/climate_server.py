import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from src.tools.climate_tool import fetch_weather
from src.tools.indices_tool import calculate_indices

mcp = FastMCP("climate_server")

_CAMPOS_PADRAO = [
    "TEMPERATURA_MAXIMA_NA_HORA_ANT_AUT",
    "TEMPERATURA_MINIMA_NA_HORA_ANT_AUT",
    "TEMPERATURA_DO_AR_BULBO_SECO_HORARIA",
    "PRECIPITACAO_TOTAL_HORARIO",
    "UMIDADE_RELATIVA_DO_AR_HORARIA",
]


@mcp.tool()
def fetch_weather_tool(
    data_inicio: str,
    data_fim: str,
    estacao: str | None = None
) -> str:
    return fetch_weather(
        data_inicio,
        data_fim,
        campos=_CAMPOS_PADRAO,
        estacao=estacao
    )


@mcp.tool()
def calculate_indices_tool(serie_json: str, cultura: str) -> str:
    return calculate_indices(serie_json, cultura)


if __name__ == "__main__":
    mcp.run()