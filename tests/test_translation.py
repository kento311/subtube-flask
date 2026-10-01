import os
import unittest
from unittest.mock import Mock, patch

import requests

from services.translation import (
    MAX_TRANSLATION_LENGTH,
    TranslationInputError,
    TranslationNotConfigured,
    TranslationServiceError,
    is_translation_configured,
    translate_to_japanese,
)


class TranslationServiceTests(unittest.TestCase):
    def test_reports_unconfigured_without_an_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_translation_configured())
            with self.assertRaises(TranslationNotConfigured):
                translate_to_japanese("Hello")

    @patch("services.translation.requests.post")
    def test_uses_the_free_endpoint_for_a_free_key(self, post):
        response = Mock()
        response.json.return_value = {
            "translations": [{"text": "こんにちは"}]
        }
        post.return_value = response

        with patch.dict(
            os.environ,
            {"DEEPL_API_KEY": "example:fx", "DEEPL_API_PLAN": "auto"},
            clear=True,
        ):
            self.assertEqual(translate_to_japanese("Hello"), "こんにちは")

        post.assert_called_once_with(
            "https://api-free.deepl.com/v2/translate",
            headers={"Authorization": "DeepL-Auth-Key example:fx"},
            json={"text": ["Hello"], "target_lang": "JA"},
            timeout=8,
        )

    def test_rejects_empty_and_oversized_text(self):
        with self.assertRaises(TranslationInputError):
            translate_to_japanese("   ")
        with self.assertRaises(TranslationInputError):
            translate_to_japanese("x" * (MAX_TRANSLATION_LENGTH + 1))

    @patch("services.translation.requests.post")
    def test_hides_provider_connection_errors(self, post):
        post.side_effect = requests.Timeout("provider details")
        with patch.dict(
            os.environ,
            {"DEEPL_API_KEY": "example:fx", "DEEPL_API_PLAN": "free"},
            clear=True,
        ):
            with self.assertRaises(TranslationServiceError) as context:
                translate_to_japanese("Hello")

        self.assertNotIn("provider details", str(context.exception))


if __name__ == "__main__":
    unittest.main()
