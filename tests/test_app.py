import os
import unittest
from unittest.mock import patch

from app import app


class AppTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_home_page_marks_translation_as_disabled_without_a_key(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-translation-enabled="false"', response.data)

    def test_translation_endpoint_requires_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.post(
                "/api/translate_text", json={"text": "Hello"}
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json()["code"], "translation_not_configured"
        )

    def test_translation_endpoint_rejects_invalid_json(self):
        response = self.client.post(
            "/api/translate_text", data="not-json", content_type="text/plain"
        )

        self.assertEqual(response.status_code, 400)

    @patch("app.translate_to_japanese", return_value="こんにちは")
    def test_translation_endpoint_returns_translation(self, translate):
        response = self.client.post(
            "/api/translate_text", json={"text": "Hello"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"translation": "こんにちは"})
        translate.assert_called_once_with("Hello")


if __name__ == "__main__":
    unittest.main()
