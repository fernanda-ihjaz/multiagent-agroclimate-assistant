"""
Calcular as normais e estatísticas históricas (médias, mínimos, máximos)
da série limpa. O resultado viabiliza a comparação climatológica pelo Agente.
"""

import pandas as pd
from pathlib import Path

def calculate_climatological_normals(input_path: Path, output_path: Path):
    print(f"Carregando dados limpos de: {input_path}")
    df = pd.read_parquet(input_path)

    if 'DATETIME' not in df.columns:
        raise ValueError("A coluna DATETIME é obrigatória para o cálculo das normais.")

    df['MES'] = df['DATETIME'].dt.month

    colunas_interesse = [col for col in df.columns if any(
        chave in col for chave in ["TEMPERATURA", "PRECIPITACAO", "UMIDADE"]
    )]

    print("Calculando médias históricas (Normais Climatológicas Mensais)...")
    
    agrupamento = ['ESTACAO', 'CODIGO_WMO', 'MES']
    normais_mensais = df.groupby(agrupamento)[colunas_interesse].mean(numeric_only=True).reset_index()
    normais_mensais[colunas_interesse] = normais_mensais[colunas_interesse].round(2)

    print(f"Salvando base de estatísticas em: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    normais_mensais.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)
    
    csv_path = output_path.with_suffix('.csv')
    normais_mensais.to_csv(csv_path, index=False, decimal=',', sep=';')
    
    print(f"Arquivo de normais mensais (CSV) exportado em: {csv_path}")
    print("Estatísticas históricas calculadas com sucesso!")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    INPUT_FILE = BASE_DIR / "data/inmet" / "inmet_rs_cleaned.parquet"
    OUTPUT_FILE = BASE_DIR / "data/inmet" / "inmet_normals.parquet"
    
    calculate_climatological_normals(INPUT_FILE, OUTPUT_FILE)