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
        "trigo",
        "--cultura",
        "-u",
        help="Cultura analisada: trigo ou soja."
    ),
    data_inicio: str = typer.Option(
        None,
        "--inicio",
        "-i",
        help="Data de início no formato YYYY-MM-DD."
    ),
    data_fim: str = typer.Option(
        None,
        "--fim",
        "-f",
        help="Data de fim no formato YYYY-MM-DD."
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
    logger.info(f"Pergunta      : {pergunta}")
    logger.info(f"Cultura       : {cultura}")
    logger.info(f"Período       : {data_inicio} -> {data_fim}")
    logger.info(f"Estação       : {estacao}")
    logger.info(f"Categoria RAG : {categoria}")
    logger.info(f"Top K         : {top_k}")
    logger.info(f"Incluir risco : {incluir_risco}")

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

        logger.info("Consulta finalizada com sucesso.")
        logger.info(f"Tamanho da resposta: {len(resposta)} caracteres")

        typer.echo(resposta)

    except Exception:
        exception("Erro durante a execução da consulta.")
        raise


if __name__ == "__main__":
    app()