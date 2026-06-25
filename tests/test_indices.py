"""
Testes automatizados para o cálculo de índices agroclimáticos.
Valida as lógicas matemáticas da ferramenta src/tools/indices_tool.py.
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tools.indices_tool import calculate_indices

@pytest.fixture
def mock_climate_data():
    """
    Fixture que simula o retorno da climate_tool.py com dados em JSON normalizado.
    Criamos um cenário perfeitamente controlado para calcularmos os índices na mão e 
    batermos com a saída da função.
    """
    data = [
        # Dia 1: 
        # T_media = 10 (Max 15, Min 5). Chuva = 10mm. 
        # Frio = Sim (6 < 7.2). Doença = Não (T_ar < 15)
        {
            "DATETIME": "2024-05-01 10:00:00", 
            "TEMP_MAX": 15, "TEMP_MIN": 5, 
            "TEMPERATURA_DO_AR": 6, 
            "PRECIPITACAO_TOTAL": 10, 
            "UMIDADE_REL_HORARIA": 95
        },
        # Dia 1 (ainda, afeta horas/frio/doença): 
        # Chuva = 5mm. Frio = Não. Doença = Sim (T_ar 16 está entre 15-30, Umid > 90%)
        {
            "DATETIME": "2024-05-01 11:00:00", 
            "TEMP_MAX": 15, "TEMP_MIN": 5, 
            "TEMPERATURA_DO_AR": 16, 
            "PRECIPITACAO_TOTAL": 5, 
            "UMIDADE_REL_HORARIA": 95
        },
        # Dia 2: 
        # T_media = 20 (Max 25, Min 15). Chuva = 0mm. 
        # Frio = Não. Doença = Não (Umidade <= 90%)
        {
            "DATETIME": "2024-05-02 10:00:00", 
            "TEMP_MAX": 25, "TEMP_MIN": 15, 
            "TEMPERATURA_DO_AR": 20, 
            "PRECIPITACAO_TOTAL": 0, 
            "UMIDADE_REL_HORARIA": 80
        }
    ]
    return json.dumps(data)

def test_calculo_indices_trigo(mock_climate_data):
    """
    Testa os cálculos para a cultura do Trigo (Temperatura base = 5°C).
    Expectativas calculadas:
    - Chuva total = 10 + 5 + 0 = 15mm
    - GD (Graus-dia): 
        Dia 1: max(10 - 5, 0) = 5
        Dia 2: max(20 - 5, 0) = 15
        Total GD = 20
    - Frio (< 7.2°C): 1 hora (apenas 10h do dia 1)
    - Doença: 1 hora favorável (11h do dia 1) de 3 horas totais = 33.33%
    """
    resultado_json = calculate_indices(mock_climate_data, "trigo")
    resultado = json.loads(resultado_json)

    assert "error" not in resultado, f"Erro inesperado: {resultado.get('error')}"
    assert resultado["cultura_analisada"] == "trigo"
    assert resultado["chuva_acumulada_mm"] == 15.0
    assert resultado["graus_dia_acumulados"] == 20.0
    assert resultado["horas_frio_abaixo_7_2C"] == 1
    assert resultado["horas_condicao_favoravel_doenca"] == 1
    assert resultado["indice_risco_doenca"] == 33.33

def test_calculo_indices_soja(mock_climate_data):
    """
    Testa os cálculos para a cultura da Soja (Temperatura base = 10°C).
    Expectativas calculadas:
    - GD (Graus-dia): 
        Dia 1: max(10 - 10, 0) = 0
        Dia 2: max(20 - 10, 0) = 10
        Total GD = 10
    """
    resultado_json = calculate_indices(mock_climate_data, "soja")
    resultado = json.loads(resultado_json)

    assert "error" not in resultado
    assert resultado["cultura_analisada"] == "soja"
    assert resultado["graus_dia_acumulados"] == 10.0

def test_dados_vazios():
    """
    Valida a robustez (RNF04) simulando retorno vazio.
    """
    resultado_json = calculate_indices("[]", "trigo")
    resultado = json.loads(resultado_json)
    
    assert "error" in resultado
    assert "vazia" in resultado["error"].lower()

def test_json_invalido():
    """
    Valida a robustez com string corrompida.
    """
    resultado_json = calculate_indices("string_nao_json", "trigo")
    resultado = json.loads(resultado_json)
    
    assert "error" in resultado