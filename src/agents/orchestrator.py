from src.agents.rag_agent import RAGAgent
from src.agents.risk_assessment_agent import RiskAssessmentAgent
from src.agents.review_agent import ReviewAgent
from src.rag.retriever import Retriever


class OrchestratorAgent:
    """
    fluxo:
    1. Recupera documentos relevantes no RAG
    2. Monta contexto com fonte, página e categoria
    3. Envia contexto ao RAGAgent
    4. Envia resposta técnica ao RiskAssessmentAgent
    5. Envia resultado ao ReviewAgent
    6. Retorna a resposta final revisada
    """

    def __init__(self):
        self.retriever = Retriever()
        self.rag_agent = RAGAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.review_agent = ReviewAgent()

    def _build_context(self, retrieved):
        #monta o contexto textual a partir dos documentos recuperados incluindo metadados de rastreabilidade
        documents = retrieved.get("documents", [[]])[0]
        metadatas = retrieved.get("metadatas", [[]])[0]

        if not documents:
            return ""

        context_parts = []

        for doc, meta in zip(documents, metadatas):
            filename = meta.get("filename", "fonte_desconhecida")
            page = meta.get("page", "página_desconhecida")
            category = meta.get("category", "categoria_desconhecida")

            context_parts.append(
                f"Fonte: [{filename}, página {page}]\n"
                f"Categoria: {category}\n"
                f"Trecho:\n{doc}"
            )

        return "\n\n---\n\n".join(context_parts)

    def run(
        self,
        question,
        category=None,
        top_k=5,
        include_risk=True
    ):
        #executa o fluxo multiagente
        retrieved = self.retriever.search(
            query=question,
            top_k=top_k,
            category=category
        )

        context = self._build_context(retrieved)

        if not context:
            return (
                "Não encontrei documentos relevantes na base vetorial "
                "para responder com segurança."
            )

        rag_answer = self.rag_agent.run(
            question=question,
            context=context
        )

        if include_risk:
            risk_answer = self.risk_agent.run(
                scenario=f"""
Pergunta do usuário:
{question}

Resposta técnica baseada na base documental:
{rag_answer}
"""
            )

            combined_answer = f"""
Resposta técnica baseada na base documental:

{rag_answer}

Avaliação de risco:

{risk_answer}
"""
        else:
            combined_answer = rag_answer

        final_answer = self.review_agent.run(
            answer=combined_answer
        )

        return final_answer