import json
from src.agents.intent_agent import IntentAgent
from src.agents.climatology_agent import ClimatologyAgent
from src.agents.rag_agent import RAGAgent
from src.agents.risk_assessment_agent import RiskAssessmentAgent
from src.agents.review_agent import ReviewAgent
from src.rag.retriever import Retriever


class OrchestratorAgent:

    def __init__(self):
        self.intent_agent = IntentAgent()
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
            parts.append(f"[{filename}, página {page}]\n{doc}")

        return "\n\n".join(parts)

    def run(
        self,
        question: str,
        cultura: str = None,
        data_inicio: str = None,
        data_fim: str = None,
        estacao: str = "PASSO FUNDO",
        category: str = None,
        top_k: int = 5,
        include_risk: bool = True
    ):
        intent = self.intent_agent.run(question)

        cultura_final = cultura or intent.get("cultura", "trigo")
        data_inicio_final = data_inicio or intent.get("data_inicio")
        data_fim_final = data_fim or intent.get("data_fim")
        doenca = intent.get("doenca")
        tem_comparacao = intent.get("tem_comparacao", False)
        data_inicio_comp = intent.get("data_inicio_comparacao")
        data_fim_comp = intent.get("data_fim_comparacao")

        clim_principal = self.climatology_agent.run(
            question=question,
            cultura=cultura_final,
            data_inicio=data_inicio_final,
            data_fim=data_fim_final,
            estacao=estacao
        )

        clim_comparacao = None
        if tem_comparacao and data_inicio_comp and data_fim_comp:
            clim_comparacao = self.climatology_agent.run(
                question=question,
                cultura=cultura_final,
                data_inicio=data_inicio_comp,
                data_fim=data_fim_comp,
                estacao=estacao
            )

        query_rag = question
        if doenca:
            query_rag = f"{doenca} {cultura_final} condições climáticas risco {question}"

        retrieved = self.retriever.search(
            query=query_rag,
            top_k=top_k,
            category=category
        )

        context = self._build_context(retrieved)

        if not context:
            rag_answer = "Não encontrei documentos relevantes na base vetorial para complementar a análise climática."
        else:
            rag_answer = self.rag_agent.run(question=question, context=context)

        synthesis_parts = {
            "pergunta": question,
            "cultura": cultura_final,
            "periodo_principal": f"{data_inicio_final} a {data_fim_final}",
            "estacao": estacao,
            "indices_principais": clim_principal.get("indices", {}),
            "analise_climatologica_principal": clim_principal.get("interpretation", ""),
            "conhecimento_documental": rag_answer,
        }

        if clim_comparacao:
            synthesis_parts["periodo_comparacao"] = f"{data_inicio_comp} a {data_fim_comp}"
            synthesis_parts["indices_comparacao"] = clim_comparacao.get("indices", {})
            synthesis_parts["analise_climatologica_comparacao"] = clim_comparacao.get("interpretation", "")

        if include_risk:
            risk_input = json.dumps(synthesis_parts, indent=2, ensure_ascii=False)
            risk_answer = self.risk_agent.run(scenario=risk_input)
            synthesis_parts["avaliacao_de_risco"] = risk_answer

        return self.review_agent.run(synthesis=synthesis_parts, question=question)