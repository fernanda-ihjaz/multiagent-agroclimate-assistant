"""
Parte deste script foi desenvolvida com auxílio de IA generativa (Claude, da Anthropic), 
com especificação, revisão e validação feitas pela equipe.

O script realiza uma análise exploratória dos arquivos CSV do INMET, 
extraindo estatísticas e gerando um relatório de qualidade dos dados. 
Ele é projetado para ser executado localmente.

Os relatórios gerados são salvos na pasta "data/data_analysis".

Exemplos de execução:
- Análise geral de um ano específico:
  python scripts/inmet_data_analysis.py 2025

- Análise filtrada por UF e estação:
  python scripts/inmet_data_analysis.py 2025 RS PASSO FUNDO

# Os relatórios estão disponíveis em: data/data_analysis/ no repositório do projeto.
"""

import os
import sys
import csv
import glob
import math
import random
import itertools
import unicodedata
from collections import Counter
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
_CANDIDATE_DATA_DIRS = [
    os.path.join(PROJECT_ROOT, "data", "inmet"),
    os.path.join(os.getcwd(), "data", "inmet"),
]
DATA_INMET_DIR = next((p for p in _CANDIDATE_DATA_DIRS if os.path.isdir(p)),
                      _CANDIDATE_DATA_DIRS[0])
OUTPUT_DIR = os.path.join(os.path.dirname(DATA_INMET_DIR), "data_analysis")

ENCODING = "latin-1"
DELIMITER = ";"
METADATA_LINES = 8
RESERVOIR_CAP = 120_000
DISTINCT_CAP = 100_000
SEP = "-" * 35

_COLUMN_RULES = [
    (["HORA", "UTC"],                   "HORA_UTC",            "UTC"),
    (["DATA"],                          "DATA",                "-"),
    (["PRECIPITA"],                     "PRECIPITACAO_TOTAL",  "mm"),
    (["PRESS", "MAX"],                  "PRESSAO_ATM_MAX",     "mB"),
    (["PRESS", "MIN"],                  "PRESSAO_ATM_MIN",     "mB"),
    (["PRESS"],                         "PRESSAO_ATM_ESTACAO", "mB"),
    (["RADIACAO"],                      "RADIACAO_GLOBAL",     "Kj/m2"),
    (["TEMPERATURA", "ORVALHO", "MAX"], "TEMP_ORVALHO_MAX",    "C"),
    (["TEMPERATURA", "ORVALHO", "MIN"], "TEMP_ORVALHO_MIN",    "C"),
    (["TEMPERATURA", "ORVALHO"],        "TEMP_PONTO_ORVALHO",  "C"),
    (["TEMPERATURA", "MAX"],            "TEMP_MAX",            "C"),
    (["TEMPERATURA", "MIN"],            "TEMP_MIN",            "C"),
    (["TEMPERATURA", "BULBO"],          "TEMP_AR_BULBO_SECO",  "C"),
    (["UMIDADE", "MAX"],                "UMIDADE_REL_MAX",     "%"),
    (["UMIDADE", "MIN"],                "UMIDADE_REL_MIN",     "%"),
    (["UMIDADE"],                       "UMIDADE_REL_HORARIA", "%"),
    (["VENTO", "DIRE"],                 "VENTO_DIRECAO",       "gr"),
    (["VENTO", "RAJADA"],               "VENTO_RAJADA_MAX",    "m/s"),
    (["VENTO", "VELOCIDADE"],           "VENTO_VELOCIDADE",    "m/s"),
]

KNOWN_BOUNDS = {
    "UMIDADE_REL_MAX": (0, 100),
    "UMIDADE_REL_MIN": (0, 100),
    "UMIDADE_REL_HORARIA": (0, 100),
    "VENTO_DIRECAO": (0, 360),
    "PRECIPITACAO_TOTAL": (0, 1000),
    "VENTO_RAJADA_MAX": (0, 150),
    "VENTO_VELOCIDADE": (0, 150),
}

BOOL_TOKENS = {"0", "1", "SIM", "NAO", "TRUE", "FALSE", "S", "N",
               "VERDADEIRO", "FALSO"}
BLOCKS = "▁▂▃▄▅▆▇█"


def strip_accents(text):
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper()


def slugify(text):
    base = strip_accents(text)
    out = []
    for ch in base:
        if ch.isalnum():
            out.append(ch)
        elif ch in " -/":
            out.append("_")
    slug = "".join(out)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def canonical_column(raw_name):
    norm = strip_accents(raw_name)
    for words, canon, unit in _COLUMN_RULES:
        if all(w in norm for w in words):
            return canon, unit
    return slugify(raw_name) or "COLUNA", "-"


def to_float_br(value):
    if value is None:
        return None
    v = value.strip()
    if v == "":
        return None
    v = v.replace(".", "").replace(",", ".") if ("," in v and "." in v) else v.replace(",", ".")
    if v.startswith("."):
        v = "0" + v
    elif v.startswith("-."):
        v = "-0" + v[1:]
    try:
        return float(v)
    except ValueError:
        return None


def parse_date(s):
    s = s.strip()
    if not s:
        return None
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def freq_label(seconds):
    table = [
        (3600, "horária"),
        (1800, "semi-horária (30 min)"),
        (600, "10 minutos"),
        (86400, "diária"),
        (604800, "semanal"),
    ]
    for s, label in table:
        if seconds == s:
            return label
    if 28 * 86400 <= seconds <= 31 * 86400:
        return "mensal"
    if seconds % 3600 == 0:
        return f"a cada {seconds // 3600} h"
    if seconds % 60 == 0:
        return f"a cada {seconds // 60} min"
    return f"a cada {seconds} s"


class ColumnAggregator:
    def __init__(self, canon, unit, rng):
        self.canon = canon
        self.unit = unit
        self.rng = rng
        self.bounds = KNOWN_BOUNDS.get(canon)
        self.total = 0
        self.present = 0
        self.n_numeric = 0
        self.n_integer = 0
        self.n_date = 0
        self.invalid_numeric = 0
        self.out_of_range = 0
        self.sum = 0.0
        self.sumsq = 0.0
        self.min = None
        self.max = None
        self.reservoir = []
        self.seen_numeric = 0
        self.sampled = False
        self.distinct = set()
        self.distinct_trunc = False
        self.raw_sample = set()

    def add(self, raw):
        self.total += 1
        if raw is None:
            return
        v = raw.strip()
        if v == "":
            return
        self.present += 1
        h = hash(v)
        if not self.distinct_trunc:
            if len(self.distinct) < DISTINCT_CAP:
                self.distinct.add(h)
            else:
                self.distinct_trunc = True
        if len(self.raw_sample) < 12:
            self.raw_sample.add(strip_accents(v))
        x = to_float_br(v)
        if x is not None:
            self.n_numeric += 1
            if x.is_integer():
                self.n_integer += 1
            self.sum += x
            self.sumsq += x * x
            if self.min is None or x < self.min:
                self.min = x
            if self.max is None or x > self.max:
                self.max = x
            if self.bounds and not (self.bounds[0] <= x <= self.bounds[1]):
                self.out_of_range += 1
            self.seen_numeric += 1
            if len(self.reservoir) < RESERVOIR_CAP:
                self.reservoir.append(x)
            else:
                self.sampled = True
                j = self.rng.randint(0, self.seen_numeric - 1)
                if j < RESERVOIR_CAP:
                    self.reservoir[j] = x
        else:
            if parse_date(v):
                self.n_date += 1

    def infer_type(self):
        if self.present == 0:
            return "vazio"
        if self.n_date == self.present:
            return "data"
        distinct_n = len(self.distinct)
        if distinct_n <= 2 and self.raw_sample and self.raw_sample.issubset(BOOL_TOKENS):
            return "booleano"
        if self.n_numeric == self.present:
            return "inteiro" if self.n_integer == self.n_numeric else "decimal"
        return "texto"

    def finalize(self):
        tipo = self.infer_type()
        st = {
            "canon": self.canon,
            "unit": self.unit,
            "tipo": tipo,
            "total": self.total,
            "present": self.present,
            "missing": self.total - self.present,
            "missing_pct": ((self.total - self.present) / self.total * 100) if self.total else 0.0,
            "unicos": len(self.distinct),
            "unicos_trunc": self.distinct_trunc,
            "numeric": tipo in ("inteiro", "decimal"),
            "out_of_range": self.out_of_range,
            "invalid_numeric": (self.present - self.n_numeric) if tipo in ("inteiro", "decimal") else 0,
        }
        if st["numeric"] and self.present:
            n = self.n_numeric
            mean = self.sum / n
            var = max(self.sumsq / n - mean * mean, 0.0)
            res = sorted(self.reservoir)
            q1 = _percentile(res, 25)
            q2 = _percentile(res, 50)
            q3 = _percentile(res, 75)
            st.update({
                "min": self.min, "max": self.max, "mean": mean,
                "std": math.sqrt(var), "median": q2, "p25": q1, "p75": q3,
                "sampled": self.sampled, "reservoir": res,
            })
            iqr = (q3 - q1) if (q1 is not None and q3 is not None) else 0.0
            lo = q1 - 1.5 * iqr if q1 is not None else None
            hi = q3 + 1.5 * iqr if q3 is not None else None
            st["fence_lo"], st["fence_hi"] = lo, hi
            if res and lo is not None and hi is not None and iqr > 0:
                out_sample = sum(1 for v in res if v < lo or v > hi)
                frac = out_sample / len(res)
                st["outliers"] = round(frac * self.present)
                st["outliers_pct"] = frac * 100
            else:
                st["outliers"] = 0
                st["outliers_pct"] = 0.0
        return st


def _percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def sparkline(reservoir, lo, hi, nbins=12):
    if not reservoir or lo is None or hi is None or hi == lo:
        return "·" * nbins
    width = (hi - lo) / nbins
    counts = [0] * nbins
    for v in reservoir:
        idx = int((v - lo) / width)
        if idx >= nbins:
            idx = nbins - 1
        if idx < 0:
            idx = 0
        counts[idx] += 1
    mx = max(counts)
    chars = []
    for c in counts:
        if c == 0:
            chars.append(" ")
        else:
            level = 1 + int((c / mx) * (len(BLOCKS) - 1))
            chars.append(BLOCKS[min(level, len(BLOCKS) - 1)])
    return "".join(chars)


def read_metadata(path):
    metadata = {}
    columns = []
    with open(path, encoding=ENCODING, newline="") as f:
        head = list(itertools.islice(f, METADATA_LINES + 1))
    for line in head[:METADATA_LINES]:
        line = line.rstrip("\r\n")
        if DELIMITER in line:
            key, _, val = line.partition(DELIMITER)
            key = strip_accents(key.strip().rstrip(":").strip())
            key = key.replace(" ", "_").replace("(", "").replace(")", "")
            metadata[key] = val.strip()
    if len(head) > METADATA_LINES:
        header_line = head[METADATA_LINES].rstrip("\r\n")
        raw_cols = header_line.split(DELIMITER)
        while raw_cols and raw_cols[-1].strip() == "":
            raw_cols.pop()
        for raw in raw_cols:
            canon, unit = canonical_column(raw)
            columns.append((canon, unit, raw))
    return metadata, columns


def iter_data_rows(path):
    with open(path, encoding=ENCODING, newline="") as f:
        head = list(itertools.islice(f, METADATA_LINES + 1))
        metadata = {}
        for line in head[:METADATA_LINES]:
            line = line.rstrip("\r\n")
            if DELIMITER in line:
                key, _, val = line.partition(DELIMITER)
                key = strip_accents(key.strip().rstrip(":").strip())
                key = key.replace(" ", "_").replace("(", "").replace(")", "")
                metadata[key] = val.strip()
        header_line = head[METADATA_LINES].rstrip("\r\n") if len(head) > METADATA_LINES else ""
        raw_cols = header_line.split(DELIMITER)
        while raw_cols and raw_cols[-1].strip() == "":
            raw_cols.pop()
        columns = [(*canonical_column(raw), raw) for raw in raw_cols]
        n = len(columns)
        reader = csv.reader(f, delimiter=DELIMITER)
        for fields in reader:
            if not any(fld.strip() for fld in fields):
                continue
            fields = (fields + [""] * n)[:n]
            yield metadata, columns, fields


def discover_files(year):
    year_dir = os.path.join(DATA_INMET_DIR, str(year))
    if not os.path.isdir(year_dir):
        return [], year_dir
    files = []
    for pat in ("*.csv", "*.CSV"):
        files.extend(glob.glob(os.path.join(year_dir, pat)))
    return sorted(set(files)), year_dir


class DatasetProfile:
    def __init__(self):
        self.rng = random.Random(0)
        self.agg = {}
        self.order = []
        self.col_original = {}
        self.total_records = 0
        self.stations = []
        self.by_uf = {}
        self.min_date = None
        self.max_date = None
        self.days = set()
        self.delta_counter = Counter()
        self.dup_timestamps = 0
        self.schemas = set()
        self.total_bytes = 0
        self.lat_vals = []
        self.lon_vals = []

    def _get_agg(self, canon, unit):
        if canon not in self.agg:
            self.agg[canon] = ColumnAggregator(canon, unit, self.rng)
            self.order.append(canon)
        return self.agg[canon]

    def add_file(self, path):
        try:
            self.total_bytes += os.path.getsize(path)
        except OSError:
            pass
        md_seen = None
        n_rows = 0
        first_date = None
        last_date = None
        data_idx = hora_idx = None
        prev_ts = None
        seen_keys = set()
        for metadata, columns, row in iter_data_rows(path):
            if md_seen is None:
                md_seen = metadata
                for (canon, unit, raw) in columns:
                    self._get_agg(canon, unit)
                    self.col_original[canon] = raw
                data_idx = next((i for i, c in enumerate(columns) if c[0] == "DATA"), None)
                hora_idx = next((i for i, c in enumerate(columns) if c[0] == "HORA_UTC"), None)
                self.schemas.add(tuple(c[0] for c in columns))
            n_rows += 1
            for idx, (canon, unit, raw) in enumerate(columns):
                self.agg[canon].add(row[idx])
            if data_idx is not None:
                d = parse_date(row[data_idx])
                hora_raw = row[hora_idx].strip() if hora_idx is not None and hora_idx < len(row) else ""
                if d:
                    self.days.add(d.date())
                    if first_date is None or d < first_date:
                        first_date = d
                    if last_date is None or d > last_date:
                        last_date = d
                    self.min_date = d if self.min_date is None or d < self.min_date else self.min_date
                    self.max_date = d if self.max_date is None or d > self.max_date else self.max_date
                    key = (row[data_idx].strip(), hora_raw)
                    if key in seen_keys:
                        self.dup_timestamps += 1
                    else:
                        seen_keys.add(key)
                    ts = d
                    if len(hora_raw) >= 4 and hora_raw[:4].isdigit():
                        try:
                            ts = d.replace(hour=int(hora_raw[:2]), minute=int(hora_raw[2:4]))
                        except ValueError:
                            ts = d
                    if prev_ts is not None and ts > prev_ts:
                        self.delta_counter[int((ts - prev_ts).total_seconds())] += 1
                    prev_ts = ts
        if md_seen is None:
            return
        self.total_records += n_rows
        uf = md_seen.get("UF", "??")
        est = md_seen.get("ESTACAO", "??")
        self.by_uf.setdefault(uf, set()).add(est)
        lat = to_float_br(md_seen.get("LATITUDE", ""))
        lon = to_float_br(md_seen.get("LONGITUDE", ""))
        if lat is not None:
            self.lat_vals.append(lat)
        if lon is not None:
            self.lon_vals.append(lon)
        self.stations.append({
            "metadata": md_seen,
            "n_rows": n_rows,
            "first": first_date.strftime("%Y-%m-%d") if first_date else "—",
            "last": last_date.strftime("%Y-%m-%d") if last_date else "—",
        })

    def column_stats(self):
        return [self.agg[c].finalize() for c in self.order]


def fmt_num(x, nd=2):
    if x is None:
        return "—"
    return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(n):
    return f"{n:,}".replace(",", ".")


def quality_label(completude, dup_pct, invalid_total, schema_ok):
    if completude >= 95 and dup_pct == 0 and invalid_total == 0 and schema_ok:
        return "Excelente"
    if completude >= 85 and dup_pct < 1 and schema_ok:
        return "Boa"
    if completude >= 70:
        return "Regular"
    return "Ruim"


def build_report(year, profile, n_files, scope):
    stats = profile.column_stats()
    numeric_stats = [s for s in stats if s["numeric"]]
    n_cols = len(profile.order)
    total_cells = profile.total_records * n_cols
    present_cells = sum(s["present"] for s in stats)
    completude = (present_cells / total_cells * 100) if total_cells else 0.0
    dup_pct = (profile.dup_timestamps / profile.total_records * 100) if profile.total_records else 0.0
    invalid_total = sum(s["invalid_numeric"] for s in stats)
    out_of_range_total = sum(s["out_of_range"] for s in stats)
    schema_ok = len(profile.schemas) <= 1

    L = []
    L.append(scope["title"])
    L.append(f"Ano: {year}   |   Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    L.append(SEP)

    L.append("VISÃO GERAL")
    L.append(f"Arquivos : {fmt_int(n_files)}")
    L.append(f"Linhas   : {fmt_int(profile.total_records)}")
    L.append(f"Colunas  : {fmt_int(n_cols)}")
    L.append(f"Volume   : {fmt_num(profile.total_bytes / (1024*1024), 2)} MB")
    L.append(SEP)

    L.append("COBERTURA TEMPORAL")
    if profile.min_date and profile.max_date:
        span = (profile.max_date.date() - profile.min_date.date()).days + 1
        L.append(f"Período         : {profile.min_date.strftime('%Y-%m-%d')} a {profile.max_date.strftime('%Y-%m-%d')}")
        L.append(f"Intervalo       : {span} dia(s)")
        L.append(f"Dias com dados  : {len(profile.days)}")
    else:
        L.append("Sem datas válidas.")
    L.append(SEP)

    L.append("FREQUÊNCIA DOS REGISTROS")
    if profile.delta_counter:
        modal, cnt = profile.delta_counter.most_common(1)[0]
        share = cnt / sum(profile.delta_counter.values()) * 100
        L.append(f"Frequência predominante : {freq_label(modal)} ({fmt_num(share,1)}% dos intervalos)")
    else:
        L.append("Não foi possível determinar.")
    L.append(SEP)

    L.append("COBERTURA GEOGRÁFICA")
    L.append(f"Estações : {len(profile.stations)}")
    L.append(f"UFs      : {len(profile.by_uf)} ({', '.join(sorted(profile.by_uf))})")
    if profile.lat_vals and profile.lon_vals:
        L.append(f"Latitude  : {fmt_num(min(profile.lat_vals),4)} a {fmt_num(max(profile.lat_vals),4)}")
        L.append(f"Longitude : {fmt_num(min(profile.lon_vals),4)} a {fmt_num(max(profile.lon_vals),4)}")
    L.append(SEP)

    L.append("COLUNAS (nome, tipo, ausentes, únicos)")
    for i, s in enumerate(stats, 1):
        original = profile.col_original.get(s["canon"], s["canon"])
        uniq = f"{fmt_int(s['unicos'])}" + ("+" if s["unicos_trunc"] else "")
        L.append(f"[{i:02d}] {original}")
        L.append(f"     canônico: {s['canon']} | tipo: {s['tipo']} | "
                 f"ausentes: {fmt_int(s['missing'])} ({fmt_num(s['missing_pct'],1)}%) | "
                 f"únicos: {uniq}")
    L.append(SEP)

    L.append("ESTATÍSTICAS NUMÉRICAS (mín, máx, média, mediana)")
    if numeric_stats:
        L.append(f"{'COLUNA':<22}{'UN':<6}{'MÍN':>11}{'MÁX':>11}{'MÉDIA':>11}{'MEDIANA':>11}")
        for s in numeric_stats:
            mark = "*" if s.get("sampled") else ""
            L.append(f"{s['canon']:<22}{s['unit']:<6}{fmt_num(s.get('min')):>11}"
                     f"{fmt_num(s.get('max')):>11}{fmt_num(s.get('mean')):>11}"
                     f"{fmt_num(s.get('median')):>10}{mark}")
        if any(s.get("sampled") for s in numeric_stats):
            L.append(f"* mediana estimada por amostragem (> {fmt_int(RESERVOIR_CAP)} valores).")
    else:
        L.append("Nenhuma coluna numérica.")
    L.append(SEP)

    L.append("DISTRIBUIÇÃO DOS DADOS (histograma min→max)")
    for s in numeric_stats:
        spark = sparkline(s.get("reservoir"), s.get("min"), s.get("max"))
        L.append(f"{s['canon']:<22} {spark}  [{fmt_num(s.get('min'),1)} a {fmt_num(s.get('max'),1)}]")
    L.append(SEP)

    L.append("OUTLIERS (regra do IQR, fora de Q1-1.5*IQR .. Q3+1.5*IQR)")
    for s in numeric_stats:
        L.append(f"{s['canon']:<22} {fmt_int(s.get('outliers',0)):>8} "
                 f"({fmt_num(s.get('outliers_pct',0.0),1)}%) | "
                 f"faixa esperada: [{fmt_num(s.get('fence_lo'),1)} a {fmt_num(s.get('fence_hi'),1)}]")
    L.append(SEP)

    L.append("REGISTROS DUPLICADOS")
    L.append(f"Registros com (Data, Hora) repetida : {fmt_int(profile.dup_timestamps)} "
             f"({fmt_num(dup_pct,2)}%)")
    L.append(SEP)

    L.append("CONSISTÊNCIA DOS DADOS")
    L.append(f"Esquema de colunas idêntico em todos os arquivos : "
             f"{'sim' if schema_ok else 'não (' + str(len(profile.schemas)) + ' esquemas distintos)'}")
    L.append(f"Valores não numéricos em colunas numéricas       : {fmt_int(invalid_total)}")
    L.append(f"Valores fora da faixa física esperada            : {fmt_int(out_of_range_total)}")
    for s in stats:
        if s["out_of_range"]:
            L.append(f"   - {s['canon']}: {fmt_int(s['out_of_range'])} valor(es) fora da faixa")
    L.append(SEP)

    L.append("QUALIDADE GERAL DOS DADOS")
    L.append(f"Completude (células preenchidas) : {fmt_num(completude,1)}%")
    L.append(f"Duplicidade                      : {fmt_num(dup_pct,2)}%")
    L.append(f"Valores inválidos                : {fmt_int(invalid_total + out_of_range_total)}")
    L.append(f"Classificação geral              : "
             f"{quality_label(completude, dup_pct, invalid_total + out_of_range_total, schema_ok)}")

    return "\n".join(L)


def filter_by_metadata(files, uf, station_query):
    uf_norm = strip_accents(uf).strip() if uf else None
    st_norm = strip_accents(station_query).strip() if station_query else None
    selected = []
    available = []
    for path in files:
        try:
            md, _ = read_metadata(path)
        except Exception as exc:
            print(f"[AVISO] metadados ilegíveis em '{os.path.basename(path)}': {exc}")
            continue
        f_uf = strip_accents(md.get("UF", ""))
        f_est = strip_accents(md.get("ESTACAO", ""))
        f_wmo = strip_accents(md.get("CODIGO_WMO", ""))
        available.append((md.get("UF", "?"), md.get("ESTACAO", "?")))
        if uf_norm and f_uf != uf_norm:
            continue
        if st_norm and (st_norm not in f_est and st_norm != f_wmo):
            continue
        selected.append(path)
    return selected, available


def main(argv):
    if len(argv) < 2:
        print("Uso: python inmet_data_analysis.py <ANO> [UF] [ESTACAO]")
        print("Ex.: python inmet_data_analysis.py 2025")
        print("     python inmet_data_analysis.py 2025 RS PASSO FUNDO")
        return 1

    year = argv[1].strip()
    uf = argv[2].strip() if len(argv) >= 3 else None
    station = " ".join(argv[3:]).strip() if len(argv) >= 4 else None

    print(f"[INFO] Pasta de dados : {DATA_INMET_DIR}")
    print(f"[INFO] Ano            : {year}")
    if uf:
        print(f"[INFO] Filtro UF      : {uf}")
    if station:
        print(f"[INFO] Filtro estação : {station}")

    files, year_dir = discover_files(year)
    if not files:
        print(f"[ERRO] Nenhum arquivo .CSV encontrado em: {year_dir}")
        return 1
    print(f"[INFO] {len(files)} arquivo(s) encontrado(s).")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if uf or station:
        selected, available = filter_by_metadata(files, uf, station)
        if not selected:
            print(f"[ERRO] Nenhuma estação corresponde a UF='{uf}' ESTACAO='{station}'.")
            print("       Estações disponíveis neste ano:")
            for u, e in sorted(set(available)):
                print(f"         {u} - {e}")
            return 1

        print(f"[INFO] {len(selected)} arquivo(s) correspondem ao filtro. Processando...")
        profile = DatasetProfile()
        for path in selected:
            try:
                profile.add_file(path)
            except Exception as exc:
                print(f"[AVISO] falha ao processar '{os.path.basename(path)}': {exc}")

        md = profile.stations[0]["metadata"]
        uf_out = slugify(md.get("UF", uf or "UF"))
        if station:
            est_out = slugify(md.get("ESTACAO", station))
            out_path = os.path.join(OUTPUT_DIR, f"inmet_{year}_{uf_out}_{est_out}_report.txt")
            title = f"RELATÓRIO INMET — {md.get('ESTACAO','?')} ({md.get('UF','?')})"
        else:
            out_path = os.path.join(OUTPUT_DIR, f"inmet_{year}_{uf_out}_report.txt")
            title = f"RELATÓRIO INMET — UF {md.get('UF','?')}"
        report = build_report(year, profile, len(selected), {"title": title})
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] Relatório gerado: {out_path}")

    else:
        print(f"[INFO] Processando {len(files)} arquivo(s) em streaming...")
        profile = DatasetProfile()
        for i, path in enumerate(files, 1):
            try:
                profile.add_file(path)
            except Exception as exc:
                print(f"[AVISO] falha ao processar '{os.path.basename(path)}': {exc}")
            if i % 50 == 0 or i == len(files):
                print(f"       {i}/{len(files)} processados...")
        out_path = os.path.join(OUTPUT_DIR, f"general_inmet_{year}_report.txt")
        report = build_report(year, profile, len(files), {"title": f"RELATÓRIO GERAL INMET {year}"})
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] Relatório gerado: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))