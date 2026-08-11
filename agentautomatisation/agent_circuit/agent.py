from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from smolagents import LiteLLMModel, ToolCallingAgent

from .prompt import AGENT_INSTRUCTIONS
from .tools import AGENT_TOOLS


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_MODEL_ID = "mistral/mistral-large-latest"
DEFAULT_MAX_STEPS = int(os.getenv("AGENT_CIRCUIT_MAX_STEPS", "8"))


def get_model_id() -> str:
    model_id = os.getenv("MISTRAL_MODEL_ID", DEFAULT_MODEL_ID).strip()
    if "/" not in model_id:
        return f"mistral/{model_id}"
    return model_id


def agent_circuit(max_steps: int = DEFAULT_MAX_STEPS) -> ToolCallingAgent:
    return ToolCallingAgent(
        model=LiteLLMModel(
            model_id=get_model_id(),
            api_key=os.getenv("MISTRAL_API_KEY", ""),
            temperature=float(os.getenv("MISTRAL_TEMPERATURE", "0.2")),
        ),
        tools=AGENT_TOOLS,
        name="agent_tourisme_circuits",
        instructions=AGENT_INSTRUCTIONS,
        max_steps=max_steps,
    )
