import os

from flask import Flask, jsonify, render_template, request

from services.translation import (
    TranslationInputError,
    TranslationNotConfigured,
    TranslationServiceError,
    is_translation_configured,
    translate_to_japanese,
)


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


@app.route("/")
def index():
    return render_template(
        "index.html", translation_enabled=is_translation_configured()
    )


@app.route("/api/translate_text", methods=["POST"])
def translate_sentence():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON形式のリクエストが必要です。"}), 400

    text = data.get("text", "")
    try:
        translated = translate_to_japanese(text)
        return jsonify({"translation": translated})
    except TranslationInputError as error:
        return jsonify({"error": str(error)}), 400
    except TranslationNotConfigured:
        return (
            jsonify(
                {
                    "error": "翻訳機能は設定されていません。",
                    "code": "translation_not_configured",
                }
            ),
            503,
        )
    except TranslationServiceError:
        app.logger.exception("Translation provider request failed")
        return jsonify({"error": "翻訳サービスへの接続に失敗しました。"}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port)
