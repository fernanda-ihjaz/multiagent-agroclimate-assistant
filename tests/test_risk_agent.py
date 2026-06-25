from src.agents.risk_assessment_agent import RiskAssessmentAgent


agent = RiskAssessmentAgent()

response = agent.run(
    "Temperatura mínima prevista de -2°C durante o espigamento do trigo."
)

print(response)