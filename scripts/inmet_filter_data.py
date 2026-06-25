"""
Filtra os registros do INMET por UF == RS
"""

from pathlib import Path

PASTA = Path(r"./data/inmet/2024")

arquivos_removidos = 0

for arquivo in PASTA.rglob("*"):
    if not arquivo.is_file():
        continue

    try:
        with open(arquivo, "r", encoding="latin-1") as f:
            uf_encontrada = False
            uf_rs = False

            # Lê apenas o cabeçalho
            for _ in range(20):
                linha = f.readline()
                if not linha:
                    break

                if linha.startswith("UF:;"):
                    uf_encontrada = True
                    uf_rs = linha.strip().split(";")[1].strip() == "RS"
                    break

        if not uf_encontrada or not uf_rs:
            arquivo.unlink()
            arquivos_removidos += 1
            print(f"Removido: {arquivo}")

    except Exception as e:
        print(f"Erro em {arquivo}: {e}")

print(f"\nTotal removido: {arquivos_removidos}")