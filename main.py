import typer

from scripts.index_knowledge_base import index_knowledge_base
from src.agents.orchestrator import OrchestratorAgent
from src.utils.logger import logger, timer, exception

app = typer.Typer(
    help="Assistente agroclimático multiagente com RAG e LLM local."
)


@app.command()
def indexar():
    logger.info("Comando: indexar")

    try:
        with timer("Indexação da base de conhecimento"):
            index_knowledge_base()
        logger.info("Indexação concluída com sucesso.")
    except Exception:
        exception("Erro durante a indexação.")
        raise


@app.command()
def perguntar(
    pergunta: str = typer.Argument(
        ...,
        help="Pergunta para o assistente agroclimático."
    ),
    cultura: str = typer.Option(
        None,
        "--cultura",
        "-u",
        help="Força a cultura analisada: trigo ou soja. Se omitido, é inferido da pergunta."
    ),
    data_inicio: str = typer.Option(
        None,
        "--inicio",
        "-i",
        help="Força a data de início (YYYY-MM-DD). Se omitido, é inferido da pergunta."
    ),
    data_fim: str = typer.Option(
        None,
        "--fim",
        "-f",
        help="Força a data de fim (YYYY-MM-DD). Se omitido, é inferido da pergunta."
    ),
    estacao: str = typer.Option(
        "PASSO FUNDO",
        "--estacao",
        "-e",
        help="Nome da estação INMET."
    ),
    categoria: str = typer.Option(
        None,
        "--categoria",
        "-c",
        help="Filtro opcional para o RAG: frost, soy, wheat ou zarc."
    ),
    top_k: int = typer.Option(
        5,
        "--top-k",
        "-k",
        help="Número de trechos recuperados no RAG."
    ),
    incluir_risco: bool = typer.Option(
        True,
        "--risco/--sem-risco",
        help="Inclui ou não avaliação de risco."
    )
):
    logger.info("=" * 80)
    logger.info("Nova consulta")
    logger.info(f"Pergunta : {pergunta}")
    logger.info(f"Estação  : {estacao}")

    try:
        with timer("Execução completa da consulta"):
            agent = OrchestratorAgent()

            resposta = agent.run(
                question=pergunta,
                cultura=cultura,
                data_inicio=data_inicio,
                data_fim=data_fim,
                estacao=estacao,
                category=categoria,
                top_k=top_k,
                include_risk=incluir_risco
            )

        logger.info(f"Resposta gerada: {len(resposta)} caracteres")
        typer.echo(resposta)

    except Exception:
        exception("Erro durante a execução da consulta.")
        raise


if __name__ == "__main__":
    app()