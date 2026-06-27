import logging
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"{datetime.now():%Y-%m-%d_%H-%M-%S}.txt"

logger = logging.getLogger("agroclimate")
logger.setLevel(logging.INFO)
logger.handlers.clear()

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

console = logging.StreamHandler()
console.setFormatter(formatter)

file = logging.FileHandler(LOG_FILE, encoding="utf-8")
file.setFormatter(formatter)

logger.addHandler(console)
logger.addHandler(file)

logger.info("=" * 80)
logger.info("NOVA EXECUÇÃO")
logger.info(f"Log: {LOG_FILE.name}")
logger.info("=" * 80)

def log_execution(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        inicio = time.perf_counter()

        logger.info(f"Executando: {func.__name__}")

        try:

            resultado = func(*args, **kwargs)

            tempo = time.perf_counter() - inicio

            logger.info(
                f"Concluído: {func.__name__} ({tempo:.3f}s)"
            )

            if resultado is not None:
                texto = str(resultado)

                if len(texto) > 1000:
                    texto = texto[:1000] + "..."

                logger.info(f"Retorno: {texto}")

            return resultado

        except Exception:

            tempo = time.perf_counter() - inicio

            logger.exception(
                f"Erro em {func.__name__} ({tempo:.3f}s)"
            )

            raise

    return wrapper

@contextmanager
def timer(nome):

    inicio = time.perf_counter()

    logger.info(f"Início: {nome}")

    try:
        yield

    except Exception:

        tempo = time.perf_counter() - inicio

        logger.exception(
            f"Erro durante '{nome}' ({tempo:.3f}s)"
        )

        raise

    tempo = time.perf_counter() - inicio

    logger.info(f"Fim: {nome} ({tempo:.3f}s)")

def stage(nome):
    logger.info(f">>> {nome}")

def params(**kwargs):

    logger.info("Parâmetros:")

    for chave, valor in kwargs.items():
        logger.info(f"   {chave}: {valor}")


def response(texto, limite=1000):

    texto = str(texto)

    if len(texto) > limite:
        texto = texto[:limite] + "..."

    logger.info("Resposta:")
    logger.info(texto)

def info(msg):
    logger.info(msg)

def warning(msg):
    logger.warning(msg)

def error(msg):
    logger.error(msg)

def debug(msg):
    logger.debug(msg)

def exception(msg):
    logger.exception(msg)