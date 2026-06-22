import typer

from scripts.index_knowledge_base import index_knowledge_base
from src.agents.orchestrator import OrchestratorAgent


app = typer.Typer(
    help="Assistente agroclimático multiagente com RAG e LLM local."
)


@app.command()
def indexar():
    #indexa os PDFs da pasta data/docs no Chroma vectorstore
    index_knowledge_base()

@app.command()
def perguntar(
    pergunta: str = typer.Argument(
        ...,
        help="Pergunta para o assistente agroclimático."
    ),
    categoria: str = typer.Option(
        None,
        "--categoria",
        "-c",
        help="Filtro opcional: frost, soy, wheat ou zarc."
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
    #faz uma pergunta ao sistema multiagente.

    agent = OrchestratorAgent()

    resposta = agent.run(
        question=pergunta,
        category=categoria,
        top_k=top_k,
        include_risk=incluir_risco
    )

    typer.echo(resposta)


if __name__ == "__main__":
    app()