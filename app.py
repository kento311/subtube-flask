import json
import os
import subprocess
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


@app.route("/api/transcript/<video_id>")
def get_transcript(video_id):
    try:
        command = [
            "youtube_transcript_api",
            video_id,
            "--format",
            "json",
            "--languages",
            "ja",
            "en",
        ]
        result = subprocess.check_output(command, stderr=subprocess.STDOUT)
        if not result:
            return jsonify({"error": "字幕データが空でした"})

        raw_data = json.loads(result)
        transcript = (
            raw_data[0]
            if (
                isinstance(raw_data, list)
                and raw_data
                and isinstance(raw_data[0], list)
            )
            else raw_data
        )
        return jsonify(transcript)
    except subprocess.CalledProcessError as error:
        error_message = error.output.decode()
        return jsonify({"error": "字幕取得エラー: " + error_message})
    except Exception as error:
        return jsonify({"error": str(error)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
