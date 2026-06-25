"""
Ler todos os arquivos
Extrair metadados
Criar DATETIME
Concatenar tudo em um único DataFrame
Salvar em Parquet

"""

from pathlib import Path
import pandas as pd
import unicodedata

# Remove acentos e caracteres problemáticos dos nomes das colunas
def normalize_column_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", str(name))
    name = name.encode("ascii", "ignore").decode("ascii")

    return (
        name.strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "PCT")
        .replace(",", "")
        .upper()
    )

# Lê um arquivo bruto do INMET e retorna um DataFrame
def read_inmet_file(filepath: str | Path) -> pd.DataFrame:
    filepath = Path(filepath)

    encodings = [
        "utf-8",
        "cp1252",
        "latin-1",
    ]

    lines = None
    encoding_used = None

    for encoding in encodings:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                lines = f.readlines()

            encoding_used = encoding
            break

        except UnicodeDecodeError:
            continue

    if lines is None:
        raise ValueError(
            f"Não foi possível identificar o encoding de {filepath}"
        )

    metadata = {}
    header_line_idx = None

    for idx, line in enumerate(lines):

        line = line.strip()

        if line.startswith("Data;"):
            header_line_idx = idx
            break

        if ":;" in line:
            key, value = line.split(":;", maxsplit=1)

            key = key.strip()
            value = value.strip()

            metadata[key] = value

    if header_line_idx is None:
        raise ValueError(
            f"Cabeçalho de dados não encontrado em {filepath}"
        )

    df = pd.read_csv(
        filepath,
        sep=";",
        encoding=encoding_used,
        skiprows=header_line_idx,
        decimal=",",
        dtype=str,
        na_values=["", " "],
        low_memory=False,
    )

    # Remove coluna vazia criada pelo ';' final
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # Normaliza nomes das colunas
    df.columns = [
        normalize_column_name(col)
        for col in df.columns
    ]

    # Adiciona metadados
    for key, value in metadata.items():

        if key in {"LATITUDE", "LONGITUDE", "ALTITUDE"}:
            try:
                value = float(
                    value.replace(",", ".")
                )
            except Exception:
                pass

        df[normalize_column_name(key)] = value

    # Cria timestamp
    data_col = next(
        (c for c in df.columns if c.startswith("DATA")),
        None,
    )

    hora_col = next(
        (c for c in df.columns if "HORA" in c),
        None,
    )

    if data_col and hora_col:

        df["DATETIME"] = pd.to_datetime(
            df[data_col].astype(str)
            + " "
            + df[hora_col]
            .astype(str)
            .str.replace(" UTC", "", regex=False),
            format="%Y/%m/%d %H%M",
            errors="coerce",
        )

    df["ARQUIVO_ORIGEM"] = filepath.name

    return df

# Carrega todos os arquivos encontrados recursivamente
def load_inmet_folder(folder: str | Path) -> pd.DataFrame:
    folder = Path(folder)

    dfs = []

    for file in folder.rglob("*"):

        if not file.is_file():
            continue

        try:
            df = read_inmet_file(file)

            dfs.append(df)

            print(
                f"[OK] {file.relative_to(folder)} "
                f"({len(df)} registros)"
            )

        except Exception as e:
            print(
                f"[ERRO] {file.relative_to(folder)}: {e}"
            )

    if not dfs:
        raise ValueError(
            f"Nenhum arquivo válido encontrado em {folder}"
        )

    return pd.concat(
        dfs,
        ignore_index=True,
        sort=False,
    )

if __name__ == "__main__":

    print("Iniciando ingestão dos dados do INMET...\n")

    df = load_inmet_folder("data/inmet")

    # Colunas categóricas para reduzir tamanho do Parquet
    for col in [
        "UF",
        "REGIAO",
        "ESTACAO",
        "CODIGO_WMO"
    ]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    output_dir = Path("data/inmet")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "inmet_rs.parquet"

    print("\nSalvando parquet...")

    df.to_parquet(
        output_file,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )

    print("\n===== RESUMO =====")
    print(f"Registros: {len(df):,}")
    print(f"Colunas: {len(df.columns)}")
    print(f"Parquet gerado: {output_file}")

    tamanho_mb = output_file.stat().st_size / (1024 * 1024)

    print(f"Tamanho: {tamanho_mb:.2f} MB")