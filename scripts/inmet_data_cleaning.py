"""
Limpar e normalizar os dados ingeridos do INMET. Converte colunas 
de texto para numéricas (tratando separador decimal), trata valores inválidos 
(como -9999) e padroniza a base para os cálculos de índices.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def clean_inmet_data(input_path: Path, output_path: Path):
    print(f"Lendo dados ingeridos de: {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado. Execute inmet_ingest.py primeiro.")
        
    df = pd.read_parquet(input_path)

    # Identifica colunas de medição climática baseada nos prefixos de interesse do INMET
    prefixos_alvo = ["TEMPERATURA", "PRECIPITACAO", "UMIDADE", "VENTO", "RADIACAO", "PRESSAO"]
    colunas_numericas = [
        col for col in df.columns 
        if any(prefix in col for prefix in prefixos_alvo)
    ]

    print(f"Limpando e tipando {len(colunas_numericas)} colunas meteorológicas...")
    
    for col in colunas_numericas:
        # Se a coluna estiver como string/object, substitui vírgula por ponto e força o numérico
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # O INMET preenche falhas de sensor com valores espúrios negativos como -9999
        df.loc[df[col] <= -9000, col] = np.nan

    # Ordenação temporal para garantir consistência em cálculos de janelas (rolling) futuros
    if 'DATETIME' in df.columns and 'ESTACAO' in df.columns:
        df = df.sort_values(by=['ESTACAO', 'DATETIME']).reset_index(drop=True)

    print(f"Salvando dados limpos em: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)
    
    # Exibe um resumo rápido dos dados faltantes pós-limpeza
    taxa_nulos = (df[colunas_numericas].isna().mean() * 100).round(2)
    print("\nResumo de Valores Nulos (%):")
    print(taxa_nulos[taxa_nulos > 0].head(10))
    print("...")
    print("\nLimpeza concluída com sucesso!")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    INPUT_FILE = BASE_DIR / "data/inmet" / "inmet_rs.parquet"
    OUTPUT_FILE = BASE_DIR / "data/inmet" / "inmet_rs_cleaned.parquet"
    
    clean_inmet_data(INPUT_FILE, OUTPUT_FILE)