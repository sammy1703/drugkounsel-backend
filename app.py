from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

from dotenv import load_dotenv
load_dotenv()

from ai.generate_counseling import generate_and_store_counseling

app = Flask(__name__)
CORS(app)  # 🔥 REQUIRED

@app.route("/")
@app.route("/health")
def home():
    return {"status": "ok"}

# ---------------- COUNSELING API ----------------
@app.route("/api/counseling", methods=["POST"])
def counseling():
    try:
        data = request.get_json(force=True)

        drug = data.get("drug", "").strip()
        lang = data.get("lang", "").strip()
        existing_drugs = data.get("existing_drugs", [])

        if not drug or not lang:
            return jsonify({"found": False}), 200

        # 🔁 LANGUAGE NORMALIZATION
        lang_map = {
            "English": "en",
            "Hindi": "hi",
            "Marathi": "mr",
            "Telugu": "te",
            "Urdu": "ur",
            "en": "en",
            "hi": "hi",
            "mr": "mr",
            "te": "te",
            "ur": "ur"
        }

        lang = lang_map.get(lang, "en")

        result = generate_and_store_counseling(drug, lang, existing_drugs)

        if not result["text"]:
            return jsonify({
                "found": False,
                "counseling": None
            })

        return jsonify({
            "found": True,
            "counseling": result["text"],
            "interactions": result.get("interactions"),
            "audio": result.get("audio")
        })

    except Exception as e:
        print("❌ COUNSELING ERROR:", e)
        return jsonify({"found": False}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
