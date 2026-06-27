import json
from datetime import datetime, timedelta
from src.agents.climatology_agent import ClimatologyAgent
from src.agents.rag_agent import RAGAgent
from src.agents.risk_assessment_agent import RiskAssessmentAgent
from src.agents.review_agent import ReviewAgent
from src.rag.retriever import Retriever


class OrchestratorAgent:

    def __init__(self):
        self.retriever = Retriever()
        self.climatology_agent = ClimatologyAgent()
        self.rag_agent = RAGAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.review_agent = ReviewAgent()

    def _build_context(self, retrieved):
        documents = retrieved.get("documents", [[]])[0]
        metadatas = retrieved.get("metadatas", [[]])[0]

        if not documents:
            return ""

        parts = []
        for doc, meta in zip(documents, metadatas):
            filename = meta.get("filename", "fonte_desconhecida")
            page = meta.get("page", "?")
            category = meta.get("category", "?")
            parts.append(
                f"Fonte: [{filename}, página {page}]\n"
                f"Categoria: {category}\n"
                f"Trecho:\n{doc}"
            )

        return "\n\n---\n\n".join(parts)

    def run(
        self,
        question: str,
        cultura: str = "trigo",
        data_inicio: str = None,
        data_fim: str = None,
        estacao: str = "PASSO FUNDO",
        category: str = None,
        top_k: int = 5,
        include_risk: bool = True
    ):
        today = datetime.today()
        if data_fim is None:
            data_fim = today.strftime("%Y-%m-%d")
        if data_inicio is None:
            data_inicio = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        climatology_result = self.climatology_agent.run(
            question=question,
            cultura=cultura,
            data_inicio=data_inicio,
            data_fim=data_fim,
            estacao=estacao
        )

        retrieved = self.retriever.search(
            query=question,
            top_k=top_k,
            category=category
        )

        context = self._build_context(retrieved)

        if not context:
            return "Não encontrei documentos relevantes na base vetorial para responder com segurança."

        rag_answer = self.rag_agent.run(question=question, context=context)

        clim_interp = climatology_result["interpretation"]
        clim_indices = json.dumps(
            climatology_result["indices"], indent=2, ensure_ascii=False
        )

        if include_risk:
            risk_scenario = (
                f"Pergunta do usuário:\n{question}\n\n"
                f"Índices agroclimáticos calculados ({data_inicio} a {data_fim} | estação: {estacao}):\n"
                f"{clim_indices}\n\n"
                f"Análise climatológica:\n{clim_interp}\n\n"
                f"Conhecimento técnico recuperado da base documental:\n{rag_answer}"
            )

            risk_answer = self.risk_agent.run(scenario=risk_scenario)

            combined = (
                f"Análise climatológica ({data_inicio} a {data_fim}):\n\n"
                f"{clim_interp}\n\n---\n\n"
                f"Base documental:\n\n{rag_answer}\n\n---\n\n"
                f"Avaliação de risco:\n\n{risk_answer}"
            )
        else:
            combined = (
                f"Análise climatológica ({data_inicio} a {data_fim}):\n\n"
                f"{clim_interp}\n\n---\n\n"
                f"Base documental:\n\n{rag_answer}"
            )

        return self.review_agent.run(answer=combined)