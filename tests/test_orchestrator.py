from src.agents.orchestrator import OrchestratorAgent


def test_orchestrator_runs_with_rag_only():
    agent = OrchestratorAgent()

    response = agent.run(
        question="Quais condições favorecem giberela no trigo?",
        category="wheat",
        top_k=3,
        include_risk=False
    )

    assert isinstance(response, str)
    assert len(response.strip()) > 0


def test_orchestrator_runs_with_risk_assessment():
    agent = OrchestratorAgent()

    response = agent.run(
        question="Qual o risco de geada para trigo em emergência?",
        category="frost",
        top_k=3,
        include_risk=True
    )

    assert isinstance(response, str)
    assert len(response.strip()) > 0
