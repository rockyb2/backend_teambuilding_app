import os
from smolagents import ToolCallingAgent, LiteLLMModel
from agentautomatisation.toolss import BuildWord, BuildPDF, BuildExcelPro, SendMail


def create_agent():
    prompt = """Tu es un assistant commercial de Ivoirtirps International.

Ton objectif est de collecter progressivement :
- Nom
- Entreprise
- Nombre de participants
- Budget
- Séjour ou journée
- Objectif
- Le transport sera pris en charge par qui
- Si c'est un séjour L'hébergement sera pris en charge par qui
- La restauration sera prise en charge par qui
- Le client a-t-il déjà organisé ou participé un événement similaire dans le passé ? Si oui, quels ont été les points positifs et négatifs de cette expérience ?


Règles importantes :
- Pose les questions une par une.
- Ne redemande jamais une information déjà donnée.
- Analyse l'historique de la conversation pour savoir ce qui a déjà été fourni.
- Tant que toutes les informations ne sont pas collectées, continue à poser les questions.
- Quand tout est complet, génère :
   1) Un résumé pour le client
   2) Un résumé structuré interne pour l'équipe commerciale que tu envera à l'adresse mail rockyb225.dev@gmail.com.
"""

    return ToolCallingAgent(
        model=LiteLLMModel(
            model_id="mistral/mistral-large-latest",
            api_key=os.getenv("MISTRAL_API_KEY")
        ),
        tools=[BuildWord(), BuildPDF(), BuildExcelPro(), SendMail()],
        max_steps=15,
        instructions=prompt
    )

agent = create_agent()
def chat_with_agent(message_user: str) -> str:
    user_input = {"message": message_user}
    output = agent.run(message_user)
    return output