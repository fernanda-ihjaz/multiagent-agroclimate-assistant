import json

import numpy as np
import pandas as pd


def calculate_indices(serie_json: str, cultura: str) -> str:
    try:
        dados = json.loads(serie_json)

        if not dados:
            return json.dumps({"error": "Série de dados vazia."})

        if isinstance(dados, dict) and "error" in dados:
            return json.dumps({"error": dados["error"]})

        df = pd.DataFrame(dados)

        if df.empty:
            return json.dumps({
                "error": "A série de dados retornada está vazia. "
                         "Verifique o período, a estação ou se os campos existem na base."
            })

        cultura = cultura.lower()
        t_base = 5.0 if cultura == "trigo" else 10.0

        indices = {
            "cultura_analisada": cultura,
            "periodo_analisado": {
                "inicio": str(df["DATETIME"].min()),
                "fim": str(df["DATETIME"].max())
            }
        }

        col_precip = next((c for c in df.columns if "PRECIP" in c), None)
        indices["chuva_acumulada_mm"] = (
            float(round(pd.to_numeric(df[col_precip], errors="coerce").sum(), 2))
            if col_precip else None
        )

        col_temp_max = next(
            (c for c in df.columns if "TEMP" in c and "MAX" in c), None
        )
        col_temp_min = next(
            (c for c in df.columns if "TEMP" in c and "MIN" in c), None
        )
        col_temp_hora = next(
            (c for c in df.columns if "TEMP" in c and ("BULBO" in c or c == "TEMPERATURA_DO_AR")),
            None
        )

        if col_temp_max and col_temp_min:
            df["DATA"] = pd.to_datetime(df["DATETIME"]).dt.date
            df[col_temp_max] = pd.to_numeric(df[col_temp_max], errors="coerce")
            df[col_temp_min] = pd.to_numeric(df[col_temp_min], errors="coerce")

            df_diario = df.groupby("DATA").agg(
                t_max=(col_temp_max, "max"),
                t_min=(col_temp_min, "min")
            ).reset_index()

            df_diario["t_media"] = (df_diario["t_max"] + df_diario["t_min"]) / 2
            df_diario["graus_dia"] = np.maximum(df_diario["t_media"] - t_base, 0)

            indices["graus_dia_acumulados"] = float(
                round(df_diario["graus_dia"].sum(), 2)
            )
        else:
            indices["graus_dia_acumulados"] = None

        if col_temp_hora:
            df[col_temp_hora] = pd.to_numeric(df[col_temp_hora], errors="coerce")
            indices["horas_frio_abaixo_7_2C"] = int(
                (df[col_temp_hora] < 7.2).sum()
            )
        else:
            indices["horas_frio_abaixo_7_2C"] = None

        col_umid = next((c for c in df.columns if "UMIDADE" in c), None)
        if col_umid and col_temp_hora:
            df[col_umid] = pd.to_numeric(df[col_umid], errors="coerce")
            condicao = (
                (df[col_umid] > 90)
                & (df[col_temp_hora] >= 15)
                & (df[col_temp_hora] <= 30)
            )
            horas_favoraveis = int(condicao.sum())
            total_horas = len(df)

            indices["indice_risco_doenca"] = (
                float(round((horas_favoraveis / total_horas) * 100, 2))
                if total_horas > 0 else 0.0
            )
            indices["horas_condicao_favoravel_doenca"] = horas_favoraveis
        else:
            indices["indice_risco_doenca"] = None

        return json.dumps(indices, indent=4)

    except Exception as e:
        return json.dumps({"error": f"Erro ao calcular índices: {str(e)}"})