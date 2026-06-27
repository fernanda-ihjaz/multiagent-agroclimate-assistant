import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd


def fetch_weather(
    data_inicio: str,
    data_fim: str,
    campos: Optional[List[str]] = None,
    estacao: Optional[str] = None
) -> str:
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / "data" / "inmet" / "inmet_rs_cleaned.parquet"

    if not data_path.exists():
        return json.dumps({"error": f"Arquivo de dados não encontrado em {data_path}."})

    try:
        inicio = pd.to_datetime(data_inicio)
        fim = pd.to_datetime(data_fim) + timedelta(days=1) - timedelta(seconds=1)

        colunas_leitura = ["DATETIME"]

        if estacao:
            colunas_leitura.append("ESTACAO")

        if campos:
            campos_upper = [c.upper() for c in campos]
            colunas_leitura = list(set(colunas_leitura + campos_upper))

        df_meta = pd.read_parquet(data_path, columns=["DATETIME"])
        mask = (pd.to_datetime(df_meta["DATETIME"]) >= inicio) & \
               (pd.to_datetime(df_meta["DATETIME"]) <= fim)
        indices_validos = df_meta[mask].index

        if len(indices_validos) == 0:
            return json.dumps([])

        df = pd.read_parquet(data_path, columns=colunas_leitura)
        df_filtrado = df.loc[indices_validos].copy()

        if estacao and "ESTACAO" in df_filtrado.columns:
            df_filtrado = df_filtrado[
                df_filtrado["ESTACAO"].str.contains(estacao.upper(), na=False)
            ]
            if campos:
                df_filtrado = df_filtrado.drop(columns=["ESTACAO"], errors="ignore")

        df_filtrado = df_filtrado.sort_values(by="DATETIME")

        if "DATETIME" in df_filtrado.columns:
            df_filtrado["DATETIME"] = pd.to_datetime(
                df_filtrado["DATETIME"]
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

        return df_filtrado.to_json(orient="records", date_format="iso")

    except Exception as e:
        return json.dumps({"error": str(e)})