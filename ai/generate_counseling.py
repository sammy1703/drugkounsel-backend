import os
import json
from openai import OpenAI
import sys

# Add parent directory to path to import tts_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tts_engine import generate_tts
except ImportError:
    def generate_tts(*args, **kwargs):
        print("⚠️ tts_engine not found, skipping voice generation")
        return None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def normalize_name(name: str) -> str:
    return (
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace("+", "plus")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


def generate_counseling_from_ai(medicine: str, lang: str):
    prompt = f"""
You are an experienced clinical pharmacist.
Generate INDIVIDUALIZED, MEDICINE-SPECIFIC patient counseling for: "{medicine}".
Language: "{lang}"

You MUST output a JSON object with a key "sections".
The value of "sections" must be a list of objects, each with "header" and "content".

REQUIRED SECTIONS:
1. WHAT IS THIS MEDICINE FOR
2. HOW TO TAKE
3. IMPORTANT WARNINGS
4. COMMON SIDE EFFECTS
5. GENERAL INSTRUCTIONS
6. DRUG FOOD INTERACTION

Example Structure:
{{
  "sections": [
    {{
      "header": "1. WHAT IS THIS MEDICINE FOR",
      "content": "Explanation in {lang}..."
    }},
    ...
  ]
}}

CONTENT RULES:
- Use simple Layman terms.
- Be specific to "{medicine}".
- Do NOT include markdown bold or stars.
- Content must be in "{lang}".
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant that outputs only JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return data.get("sections")

    except Exception as e:
        print("❌ OPENAI ERROR:", e)
        return None


def generate_interactions_section(target: str, existing: list, lang: str):
    if not existing:
        return [{
            "drug_pair": "None",
            "severity": "None",
            "description": "No other medicines provided for interaction check."
        }]

    existing_str = ", ".join(existing)

    prompt = f"""
Check drug-drug interactions between "{target}" and "{existing_str}".
Return JSON with key "interactions".
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant that outputs only JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        return json.loads(response.choices[0].message.content).get("interactions", [])

    except Exception as e:
        print("❌ INTERACTION ERROR:", e)
        return []


def generate_and_store_counseling(medicine: str, lang: str, existing_drugs: list = None):
    safe_name = normalize_name(medicine)
    lang_dir = os.path.join(BASE_DIR, "counseling_json", lang)
    os.makedirs(lang_dir, exist_ok=True)

    file_path = os.path.join(lang_dir, f"{safe_name}.json")

    base_text = None

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                base_text = json.load(f).get("ai_counseling")
        except Exception as e:
            print("❌ FILE READ ERROR:", e)

    if not base_text:
        base_text = generate_counseling_from_ai(medicine, lang)
        if base_text:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"ai_counseling": base_text}, f, ensure_ascii=False, indent=2)

    interactions = generate_interactions_section(medicine, existing_drugs, lang)

    # Convert to string if it's structured for TTS
    tts_input = base_text
    if isinstance(base_text, list):
        tts_input = "\n\n".join([f"{s['header']}\n{s['content']}" for s in base_text])

    # 4. GENERATE TTS IF NOT EXISTS
    voice_dir = os.path.join(BASE_DIR, "voice", lang)
    os.makedirs(voice_dir, exist_ok=True)
    audio_file_name = f"{safe_name}.mp3"
    audio_full_path = os.path.join(voice_dir, audio_file_name)

    if not os.path.exists(audio_full_path) and tts_input:
        try:
            generate_tts(tts_input, language=lang, output_path=audio_full_path)
        except Exception as e:
            print(f"❌ TTS ERROR: {e}")

    return {
        "text": tts_input if isinstance(base_text, list) else base_text,
        "sections": base_text if isinstance(base_text, list) else None,
        "interactions": interactions,
        "audio": f"/voices/{lang}/{audio_file_name}" if os.path.exists(audio_full_path) else None
    }
