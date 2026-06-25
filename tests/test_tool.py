# para rodar:
# python -m tests.test_tool

from src.tools.climate_tool import fetch_weather
from src.tools.indices_tool import calculate_indices

# Busca dados climáticos
serie_json = fetch_weather(
    "2024-05-01",
    "2024-05-10",
    campos=None
)
print("Amostra do JSON retornado:", serie_json[:100])

# Calcula índices para a cultura desejada
resultado = calculate_indices(
    serie_json,
    "trigo"
)

# Salva resultado em arquivo
with open("resultado_indices.json", "w", encoding="utf-8") as f:
    f.write(resultado)

print("Arquivo resultado_indices.json gerado com sucesso.")