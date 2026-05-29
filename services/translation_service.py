import logging
import os
from copy import deepcopy
from typing import Any


logger = logging.getLogger(__name__)


class DeepLTranslationService:
    """Petit wrapper autour de DeepL pour garder le CRUD simple.

    La traduction se fait au moment ou l'admin cree ou modifie un circuit.
    Comme ca, le site public lit directement la BDD et ne rappelle pas DeepL
    a chaque visiteur.
    """

    def __init__(self) -> None:
        self.target_lang = os.getenv("DEEPL_TARGET_LANG", "EN-US")
        self.source_lang = os.getenv("DEEPL_SOURCE_LANG", "FR")
        self._translator = None
        self._warning_logged = False

    def _auth_key(self) -> str | None:
        """Relit l'environnement pour rester compatible avec load_local_env()."""
        return (
            os.getenv("DEEPL_API_KEY")
            or os.getenv("DEEPL_AUTH_KEY")
            or os.getenv("DEEPL_KEY")
        )

    def _source_lang(self) -> str:
        return os.getenv("DEEPL_SOURCE_LANG", self.source_lang)

    def _target_lang(self) -> str:
        return os.getenv("DEEPL_TARGET_LANG", self.target_lang)

    def _warn_once(self, message: str) -> None:
        if self._warning_logged:
            return
        logger.warning(message)
        self._warning_logged = True

    def _get_translator(self):
        """Initialise DeepL seulement si on en a vraiment besoin."""
        if self._translator is not None:
            return self._translator

        auth_key = self._auth_key()
        if not auth_key:
            self._warn_once("DEEPL_API_KEY absent: les textes anglais garderont le francais.")
            return None

        try:
            import deepl
        except ImportError:
            self._warn_once("Package deepl absent: ajoute deepl dans requirements.txt.")
            return None

        self._translator = deepl.Translator(auth_key)
        return self._translator

    def translate_text(self, text: str) -> str:
        """Traduit une chaine simple, avec fallback silencieux vers le francais."""
        clean_text = text.strip()
        if not clean_text:
            return text

        translator = self._get_translator()
        if translator is None:
            return text

        try:
            result = translator.translate_text(
                text,
                source_lang=self._source_lang(),
                target_lang=self._target_lang(),
            )
            return result.text
        except Exception:
            logger.exception("Erreur DeepL: fallback vers le texte source.")
            return text

    def translate_value(self, value: Any) -> Any:
        """Traduit aussi les JSONB en conservant leur structure.

        Exemple: ["Repas inclus", {"titre": "Jour 1"}] garde la meme forme,
        mais chaque texte contenu dedans passe par DeepL.
        """
        if value is None:
            return None

        if isinstance(value, str):
            return self.translate_text(value)

        if isinstance(value, list):
            return [self.translate_value(item) for item in value]

        if isinstance(value, dict):
            return {key: self.translate_value(item) for key, item in value.items()}

        return deepcopy(value)


translation_service = DeepLTranslationService()
