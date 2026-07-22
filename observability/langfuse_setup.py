import logging
import os
import re
import hashlib
from contextlib import contextmanager, nullcontext
from typing import Any, Iterator

logger = logging.getLogger(__name__)

_LANGFUSE_CLIENT = None
_LANGFUSE_READY = False
_SMOLAGENTS_INSTRUMENTED = False

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalise_langfuse_env() -> None:
    base_url = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST")
    if not base_url:
        return

    base_url = base_url.rstrip("/")
    os.environ.setdefault("LANGFUSE_BASE_URL", base_url)
    os.environ.setdefault("LANGFUSE_HOST", base_url)
    os.environ.setdefault("LANGFUSE_OTEL_HOST", base_url)


def _has_langfuse_credentials() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def _mask_text(value: str) -> str:
    text = str(value or "")
    text = _EMAIL_RE.sub("[email masqué]", text)
    text = _PHONE_RE.sub("[telephone masqué]", text)
    return text


def _safe_session_id(session_id: str) -> str:
    return hashlib.sha256(str(session_id or "").encode("utf-8")).hexdigest()[:24]


def mask_for_langfuse(value: Any) -> Any:
    if isinstance(value, str):
        return _mask_text(value)
    if isinstance(value, dict):
        return {key: mask_for_langfuse(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_for_langfuse(item) for item in value]
    if isinstance(value, tuple):
        return tuple(mask_for_langfuse(item) for item in value)
    return value


def setup_langfuse():
    global _LANGFUSE_CLIENT, _LANGFUSE_READY, _SMOLAGENTS_INSTRUMENTED

    if _LANGFUSE_READY:
        return _LANGFUSE_CLIENT

    _normalise_langfuse_env()
    if not _has_langfuse_credentials() or not _env_flag("LANGFUSE_TRACE_CONVERSATIONS", False):
        logger.info("Langfuse tracing disabled or credentials missing.")
        return None

    try:
        from langfuse import get_client
        from openinference.instrumentation import TraceConfig
        from openinference.instrumentation.smolagents import SmolagentsInstrumentor
    except ImportError:
        logger.exception("Langfuse tracing dependencies are not installed.")
        return None

    try:
        _LANGFUSE_CLIENT = get_client()
        if not _SMOLAGENTS_INSTRUMENTED:
            trace_config = TraceConfig(
                hide_input_text=_env_flag("LANGFUSE_HIDE_LLM_INPUT_TEXT", True),
                hide_output_text=_env_flag("LANGFUSE_HIDE_LLM_OUTPUT_TEXT", True),
            )
            SmolagentsInstrumentor().instrument(config=trace_config)
            _SMOLAGENTS_INSTRUMENTED = True

        _LANGFUSE_READY = True
        logger.info("Langfuse tracing enabled.")
    except Exception:
        logger.exception("Langfuse tracing could not be initialized.")
        _LANGFUSE_CLIENT = None

    return _LANGFUSE_CLIENT


def get_langfuse_client():
    return _LANGFUSE_CLIENT or setup_langfuse()


def flush_langfuse() -> None:
    client = get_langfuse_client()
    if not client:
        return
    try:
        client.flush()
    except Exception:
        logger.exception("Langfuse flush failed.")


@contextmanager
def chatbot_trace_context(
    *,
    session_id: str,
    user_message: str,
    locale: str | None = None,
    history_message_count: int = 0,
) -> Iterator[Any]:
    client = get_langfuse_client()
    if not client:
        with nullcontext(None) as observation:
            yield observation
        return

    try:
        from langfuse import propagate_attributes
    except ImportError:
        with nullcontext(None) as observation:
            yield observation
        return

    environment = os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "development"
    trace_metadata = {
        "feature": "public-chatbot",
        "locale": locale or "unknown",
        "history_message_count": history_message_count,
        "pii_masked": True,
        "content_exported": False,
    }
    tags = ["chatbot", "site-web", "ivoirtrips"]
    safe_session_id = _safe_session_id(session_id)

    try:
        with client.start_as_current_observation(
            as_type="agent",
            name="chatbot-agent-turn",
            input={
                "message_length": len(str(user_message or "")),
                "message_present": bool(str(user_message or "").strip()),
            },
            metadata=trace_metadata,
        ) as observation:
            with propagate_attributes(
                trace_name="chatbot-agent-turn",
                session_id=safe_session_id,
                user_id=safe_session_id,
                tags=tags,
                metadata=trace_metadata,
                environment=environment,
            ):
                try:
                    yield observation
                except Exception as exc:
                    observation.update(
                        level="ERROR",
                        status_message=str(exc),
                        output={"error": str(exc.__class__.__name__)},
                    )
                    raise
    except Exception:
        logger.exception("Langfuse trace context failed.")
        with nullcontext(None) as observation:
            yield observation


def update_chatbot_trace_output(observation: Any, response: Any) -> None:
    if not observation:
        return

    try:
        content = response.get("content") if isinstance(response, dict) else response
        observation.update(
            output={
                "response_length": len(str(content or "")),
                "response_present": bool(str(content or "").strip()),
            }
        )
    except Exception:
        logger.exception("Langfuse trace output update failed.")
