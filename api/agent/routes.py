"""Routes pour l'agent commercial."""

from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agentautomatisation.agentcore import chat_with_agent
from api.dependencies import get_db
from crud import chat as crud_chat

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    locale: str | None = None


def _session_token(value: str | None) -> str:
    token = (value or "").strip()
    if not token or len(token) > 100:
        return uuid4().hex
    return token


def _normalize_response(response) -> dict:
    if isinstance(response, str):
        return {"content": response}
    if isinstance(response, dict):
        normalized = dict(response)
    else:
        try:
            normalized = dict(response)
        except Exception:
            normalized = {"content": str(response)}

    if "content" not in normalized or normalized["content"] is None:
        normalized["content"] = str(response)
    return normalized


def _history_payload(messages) -> list[dict]:
    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
        if message.content
    ]


@router.post("/chat")
def chat_with_agent_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    token = _session_token(request.session_id)
    chat_session = crud_chat.get_or_create_session(
        db,
        session_token=token,
        locale=request.locale,
    )
    previous_messages = crud_chat.get_recent_messages(db, chat_session.id)

    crud_chat.add_message(
        db,
        session_id=chat_session.id,
        role="user",
        content=request.message,
        metadata={"locale": request.locale} if request.locale else None,
    )

    response = _normalize_response(
        chat_with_agent(
            request.message,
            conversation_history=_history_payload(previous_messages),
        )
    )
    crud_chat.add_message(
        db,
        session_id=chat_session.id,
        role="assistant",
        content=str(response["content"]),
        metadata={"file_path": response.get("file_path")} if response.get("file_path") else None,
    )

    response["session_id"] = token
    return response
