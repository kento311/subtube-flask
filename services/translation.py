import os

import requests


MAX_TRANSLATION_LENGTH = 5_000
REQUEST_TIMEOUT_SECONDS = 8
DEEPL_ENDPOINTS = {
    "free": "https://api-free.deepl.com/v2/translate",
    "pro": "https://api.deepl.com/v2/translate",
}


class TranslationError(Exception):
    """Base error for translation operations."""


class TranslationInputError(TranslationError):
    """Raised when the requested text is invalid."""


class TranslationNotConfigured(TranslationError):
    """Raised when no translation provider credentials are configured."""


class TranslationServiceError(TranslationError):
    """Raised when the translation provider cannot return a valid result."""


def is_translation_configured():
    return bool(os.environ.get("DEEPL_API_KEY", "").strip())


def _deepl_endpoint(api_key):
    plan = os.environ.get("DEEPL_API_PLAN", "auto").strip().lower()
    if plan == "auto":
        plan = "free" if api_key.endswith(":fx") else "pro"
    if plan not in DEEPL_ENDPOINTS:
        raise TranslationNotConfigured(
            "DEEPL_API_PLAN must be one of: auto, free, pro"
        )
    return DEEPL_ENDPOINTS[plan]


def translate_to_japanese(text):
    if not isinstance(text, str) or not text.strip():
        raise TranslationInputError("翻訳する文字列を入力してください。")
    if len(text) > MAX_TRANSLATION_LENGTH:
        raise TranslationInputError(
            f"翻訳する文字列は{MAX_TRANSLATION_LENGTH}文字以下にしてください。"
        )

    api_key = os.environ.get("DEEPL_API_KEY", "").strip()
    if not api_key:
        raise TranslationNotConfigured("DEEPL_API_KEY is not configured")

    try:
        response = requests.post(
            _deepl_endpoint(api_key),
            headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
            json={"text": [text.strip()], "target_lang": "JA"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        translated_text = payload["translations"][0]["text"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
        raise TranslationServiceError("DeepL returned an invalid response") from error

    if not isinstance(translated_text, str) or not translated_text.strip():
        raise TranslationServiceError("DeepL returned an empty translation")
    return translated_text
