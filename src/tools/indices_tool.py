"""
calculate_indices
Calcula índices agroclimáticos (graus-dia, horas de frio, chuva acumulada, 
risco de doença composto) a partir da série temporal fornecida.
"""

import pandas as pd
import json
import numpy as np

def calculate_indices(serie_json: str, cultura: str) -> str:
    """
    Calcula índices agroclimáticos baseados na série JSON e na cultura especificada.
    
    Args:
        serie_json (str): JSON normalizado contendo os dados climáticos.
        cultura (str): 'trigo' ou 'soja'.
        
    Returns:
        str: JSON contendo os índices calculados.
    """
    try:
        dados = json.loads(serie_json)
        if not dados or "error" in dados:
            return json.dumps({"error": "Série de dados inválida ou vazia."})
            
        df = pd.DataFrame(dados)
        
        if df.empty:
            return json.dumps({
                "error": "A série de dados retornada está vazia. Verifique o período, a estação ou se os campos existem na base."
            })
            
        cultura = cultura.lower()
        
        # Mapeamento de Temperatura Base e limiares por cultura
        t_base = 5.0 if cultura == 'trigo' else 10.0
        
        indices = {
            "cultura_analisada": cultura,
            "periodo_analisado": {
                "inicio": str(df['DATETIME'].min()),
                "fim": str(df['DATETIME'].max())
            }
        }

        # Chuva Acumulada
        col_precip = next((c for c in df.columns if 'PRECIP' in c), None)
        if col_precip:
            indices["chuva_acumulada_mm"] = float(round(df[col_precip].sum(), 2))
        else:
            indices["chuva_acumulada_mm"] = None

        # Graus-dia e Horas de Frio
        col_temp_max = next((c for c in df.columns if 'TEMP' in c and 'MAX' in c), None)
        col_temp_min = next((c for c in df.columns if 'TEMP' in c and 'MIN' in c), None)
        col_temp_hora = next((c for c in df.columns if 'TEMP' in c and ('BULBO' in c or c == 'TEMPERATURA_DO_AR')), None)
        
        # Cálculo de Graus-Dia Diário
        if col_temp_max and col_temp_min:
            df['DATA'] = pd.to_datetime(df['DATETIME']).dt.date
            df_diario = df.groupby('DATA').agg({
                col_temp_max: 'max',
                col_temp_min: 'min'
            }).reset_index()
            
            df_diario['t_media'] = (df_diario[col_temp_max] + df_diario[col_temp_min]) / 2
            df_diario['graus_dia'] = np.maximum(df_diario['t_media'] - t_base, 0)
            
            indices["graus_dia_acumulados"] = float(round(df_diario['graus_dia'].sum(), 2))
        else:
            indices["graus_dia_acumulados"] = None

        # Cálculo de Horas de Frio (T < 7.2°C)
        if col_temp_hora:
            horas_frio = df[df[col_temp_hora] < 7.2].shape[0]
            indices["horas_frio_abaixo_7_2C"] = int(horas_frio)
        else:
            indices["horas_frio_abaixo_7_2C"] = None

        # Índice Composto de Risco de Doença
        col_umid = next((c for c in df.columns if 'UMIDADE' in c), None)
        if col_umid and col_temp_hora:
            condicao_doenca = (df[col_umid] > 90) & (df[col_temp_hora] >= 15) & (df[col_temp_hora] <= 30)
            horas_favoraveis = df[condicao_doenca].shape[0]
            
            total_horas = df.shape[0]
            if total_horas > 0:
                risco_pct = (horas_favoraveis / total_horas) * 100
                indices["indice_risco_doenca"] = float(round(risco_pct, 2))
                indices["horas_condicao_favoravel_doenca"] = int(horas_favoraveis)
            else:
                indices["indice_risco_doenca"] = 0.0
        else:
            indices["indice_risco_doenca"] = None

        return json.dumps(indices, indent=4)

    except Exception as e:
        return json.dumps({"error": f"Erro ao calcular índices: {str(e)}"})