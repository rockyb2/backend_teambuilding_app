"""  routes pour l'agent commercial  """

from fastapi import APIRouter, Depends, HTTPException, status
from agentautomatisation.agentcore import chat_with_agent
from pydantic import BaseModel

router = APIRouter(prefix="/api/agent", tags=["agent"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat_with_agent_endpoint(request: ChatRequest):
    response = chat_with_agent(request.message)
    # Normaliser la réponse au format attendu (dict avec 'content' et éventuellement 'file_path')
    if isinstance(response, str):
            response = {"content": response}
    elif not isinstance(response, dict):
        try:
            response = dict(response)
        except Exception:
            # En dernier recours, convertir en chaîne
            response = {"content": str(response)}

    return response
