from datetime import datetime

from sqlalchemy.orm import Session

from database.models import ChatMessage, ChatSession


def get_session_by_token(db: Session, session_token: str) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.session_token == session_token)
        .first()
    )


def get_or_create_session(
    db: Session,
    session_token: str,
    locale: str | None = None,
    source: str = "site_web",
) -> ChatSession:
    chat_session = get_session_by_token(db, session_token)
    if chat_session:
        if locale and chat_session.locale != locale:
            chat_session.locale = locale[:10]
            chat_session.updated_at = datetime.utcnow()
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        return chat_session

    chat_session = ChatSession(
        session_token=session_token,
        locale=locale[:10] if locale else None,
        source=source,
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def add_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        message_metadata=metadata or {},
    )
    db.add(message)
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.updated_at = datetime.utcnow()
        db.add(session)
    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(
    db: Session,
    session_id: int,
    limit: int = 12,
) -> list[ChatMessage]:
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))
