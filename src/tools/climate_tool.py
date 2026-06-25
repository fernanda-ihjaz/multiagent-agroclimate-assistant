"""
fetch_weather
Consulta a série tratada do INMET, filtrando por período e campos específicos, 
retornando um JSON normalizado.
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Optional, Union
from datetime import datetime, timedelta

def fetch_weather(
    data_inicio: str, 
    data_fim: str, 
    campos: Optional[List[str]] = None,
    estacao: Optional[str] = None
) -> str:
    
    """
    Busca dados climáticos históricos no arquivo parquet limpo.
    
    Args:
        data_inicio (str): Data de início no formato 'YYYY-MM-DD'.
        data_fim (str): Data de fim no formato 'YYYY-MM-DD'.
        campos (list, opcional): Lista de colunas para retornar. Retorna todas se None.
        estacao (str, opcional): Nome da estação (ex: 'PASSO FUNDO').
        
    Returns:
        str: JSON normalizado com os dados filtrados.
    """

    # Define o caminho assumindo a estrutura do repositório
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / "data" / "inmet" / "inmet_rs_cleaned.parquet"
    
    if not data_path.exists():
        return json.dumps({"error": f"Arquivo de dados não encontrado em {data_path}."})

    try:
        df = pd.read_parquet(data_path)
        
        # Filtro de datas
        inicio = pd.to_datetime(data_inicio)
        # Adiciona 23:59:59 para incluir o último dia completo
        fim = pd.to_datetime(data_fim) + timedelta(days=1) - timedelta(seconds=1)
        
        mask = (df['DATETIME'] >= inicio) & (df['DATETIME'] <= fim)
        df_filtrado = df.loc[mask]
        
        # Filtro de estação (opcional, para focar apenas em Passo Fundo, por exemplo)
        if estacao:
            if 'ESTACAO' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['ESTACAO'].str.contains(estacao.upper(), na=False)]
                
        # Filtro de campos
        if campos:
            # Sempre garantir que o DATETIME vá junto para contexto temporal
            colunas_finais = list(set(['DATETIME'] + [c.upper() for c in campos]))
            colunas_existentes = [c for c in colunas_finais if c in df_filtrado.columns]
            df_filtrado = df_filtrado[colunas_existentes]
            
        # Ordena cronologicamente
        df_filtrado = df_filtrado.sort_values(by='DATETIME')
        
        # Converte DATETIME para string no formato ISO para serialização JSON
        if 'DATETIME' in df_filtrado.columns:
            df_filtrado['DATETIME'] = df_filtrado['DATETIME'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
        # Converte para JSON (orient='records' cria uma lista de dicionários)
        resultado_json = df_filtrado.to_json(orient="records", date_format="iso")
        return resultado_json

    except Exception as e:
        return json.dumps({"error": str(e)})

# if __name__ == "__main__":
#     print(fetch_weather("2024-05-01", "2024-05-10", ["TEMPERATURA_MAX", "PRECIPITACAO_TOTAL"]))