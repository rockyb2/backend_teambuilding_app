from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel

from agentautomatisation.agent_chatbot import create_agent_chatbot
from agentautomatisation.agent_circuit.agent import agent_circuit

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_MODEL_ID = "mistral/mistral-large-latest"
DEFAULT_MANAGER_MAX_STEPS = int(os.getenv("MANAGER_AGENT_MAX_STEPS", "8"))

MANAGER_INSTRUCTIONS = """
Tu es le manager multi-agent du CRM IvoirTrips.
Tu délègues les demandes au bon agent:
- agent_chatbot: conversation client, qualification, réponses commerciales.
- agent_tourisme_circuits: CRUD des circuits touristiques dans le CRM.
""".strip()


def get_model_id() -> str:
    model_id = os.getenv("MISTRAL_MODEL_ID", DEFAULT_MODEL_ID).strip()
    if "/" not in model_id:
        return f"mistral/{model_id}"
    return model_id


def create_manager_agent(max_steps: int = DEFAULT_MANAGER_MAX_STEPS):
    agent_chatbot = create_agent_chatbot()
    agent_chatbot.description = "Agent chargé du chatbot public et de la qualification commerciale."

    agent_circuits = agent_circuit()
    agent_circuits.description = "Agent chargé du CRUD des circuits touristiques dans le CRM."

    return CodeAgent(
        tools=[],
        model=LiteLLMModel(
            model_id=get_model_id(),
            api_key=os.getenv("MISTRAL_API_KEY", ""),
            temperature=float(os.getenv("MISTRAL_TEMPERATURE", "0.2")),
        ),
        managed_agents=[agent_chatbot, agent_circuits],
        instructions=MANAGER_INSTRUCTIONS,
        max_steps=max_steps,
        name="manager_agent",
    )