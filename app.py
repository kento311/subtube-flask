import os
import sys

from flask import Flask, jsonify, render_template, request

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("エラー: 'deep-translator' がインストールされていません。")
    sys.exit(1)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/translate/<word>")
def translate_word(word):
    try:
        translator = GoogleTranslator(source="auto", target="ja")
        translated_text = translator.translate(word)
        return jsonify({"word": word, "meaning": translated_text})
    except Exception:
        return jsonify({"error": "Error"})


@app.route("/api/translate_text", methods=["POST"])
def translate_sentence():
    try:
        data = request.get_json()
        text = data.get("text", "")
        if not text:
            return jsonify({"error": "No text provided"})
        translated = GoogleTranslator(source="auto", target="ja").translate(text)
        return jsonify({"translation": translated})
    except Exception as error:
        return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
