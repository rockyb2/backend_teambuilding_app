from __future__ import annotations

import os
from time import sleep
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from smolagents import CodeAgent, LiteLLMModel

from agentautomatisation.agent_chatbot import create_agent_chatbot
from agentautomatisation.agent_circuit.agent import agent_circuit

MODELS = [
    "openrouter/inclusionai/ling-3.0-flash-vl:free",
    "openrouter/google/gemma-4-31b-it:free",
    "openrouter/google/gemma-4-26b-a4b-it:free",
    os.getenv("OPENROUTER_MODEL_ID") or os.getenv("OPENROUTER_MODEL"),
    os.getenv("NEX_AGI_MODEL_ID"),
    os.getenv("NEX_AGI_MODEL_ID2"),
    # os.getenv("MISTRAL_MODEL_ID2"),
    # os.getenv("MISTRAL_MODEL_ID3"),
    # os.getenv("ZAI_MODEL"),
]
MODELS = [model for model in MODELS if model]

def run_with_model_fallback(prompt):
    from agent_chatbot import create_agent

    if not MODELS:
        raise RuntimeError(
            "Aucun modele configure. Verifie OPENROUTER_MODEL_ID, "
            "NEX_AGI_MODEL_ID ou NEX_AGI_MODEL_ID2 dans l'environnement Docker."
        )

    last_error = None

    for model_id in MODELS:
        try:
            agent = create_agent(model_id)
            return agent.run(prompt)
        except Exception as error:
            last_error = error
            print(f"Modele echoue : {model_id} -> {error}")

    raise RuntimeError(f"Aucun modele disponible : {last_error}")


def run_with_retries(action, operation_name: str, attempts: int = 3):
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            return action()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                sleep(2 * attempt)

    raise HTTPException(
        status_code=502,
        detail=f"{operation_name} a echoue apres {attempts} essais : {last_error}",
    )

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

API_KEY_ENV_BY_PROVIDER = {
    "openrouter": "OPENROUTER_API_KEY",
    "zai": "ZAI_API_KEY",
}

OPENROUTER_MODEL_PREFIXES = (
    "anthropic/",
    "deepseek/",
    "google/",
    "meta-llama/",
    "nex-agi/",
    "nvidia/",
    "openai/",
    "qwen/",
    "x-ai/",
)


def normalize_model_id(model_id):
    model_id = (model_id or "").strip()

    if model_id.startswith("o*/"):
        model_id = f"openrouter/{model_id.removeprefix('o*/')}"

    if model_id.startswith("openrouter/"):
        return model_id

    if model_id.startswith(OPENROUTER_MODEL_PREFIXES):
        return f"openrouter/{model_id}"

    return model_id


def get_api_key_for_model(model_id):
    provider = model_id.split("/", 1)[0].lower()
    env_name = API_KEY_ENV_BY_PROVIDER.get(provider)
    if not env_name:
        return None

    api_key = os.getenv(env_name, "").strip()
    if not api_key:
        raise RuntimeError(f"{env_name} est manquant pour le modele {model_id}")

    return api_key

MANAGER_INSTRUCTIONS = """
Tu es le manager multi-agent du CRM IvoirTrips.
Tu délègues les demandes au bon agent:
- agent_chatbot: conversation client, qualification, réponses commerciales.
- agent_tourisme_circuits: CRUD des circuits touristiques dans le CRM.
""".strip()



def create_manager_agent(model_id):
    agent_chatbot = create_agent_chatbot(model_id)
    agent_chatbot.description = "Agent chargé du chatbot public et de la qualification commerciale."

    agent_circuits = agent_circuit()
    agent_circuits.description = "Agent chargé du CRUD des circuits touristiques dans le CRM."

    return CodeAgent(
        tools=[],
        model=LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("MISTRAL_API_KEY", ""),
            temperature=float(os.getenv("MISTRAL_TEMPERATURE", "0.2")),
        ),
        managed_agents=[agent_chatbot, agent_circuits],
        instructions=MANAGER_INSTRUCTIONS,
        max_steps=10,
        name="manager_agent",
    )