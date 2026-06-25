from src.agents.climatology_agent import ClimatologyAgent


agent = ClimatologyAgent()

response = agent.run(
    "Qual o efeito da geada sobre o trigo?"
)

print(response)