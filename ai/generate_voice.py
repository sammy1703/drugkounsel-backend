from openai import OpenAI
import os
import json
import time

# -------- PATHS (CONFIRMED) --------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEXT_DIR = os.path.join(BASE_DIR, "counseling_json", "ur")
VOICE_DIR = os.path.join(BASE_DIR, "voice", "ur")

client = OpenAI(max_retries=2)
VOICE = "alloy"

# ----------------------------------


def generate_voice(text, output_path):
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=VOICE,
        input=text
    )

    with open(output_path, "wb") as f:
        f.write(response.read())

    print("🔊 Generated:", os.path.basename(output_path))
    time.sleep(1.5)


def main():
    print("📂 Reading Telugu text from:", TEXT_DIR)
    print("🎧 Saving Telugu voice to :", VOICE_DIR)

    if not os.path.isdir(TEXT_DIR):
        print("❌ TEXT_DIR NOT FOUND")
        return

    os.makedirs(VOICE_DIR, exist_ok=True)

    for file in os.listdir(TEXT_DIR):
        if not file.endswith(".json"):
            continue

        medicine = file.replace(".json", "")
        audio_path = os.path.join(VOICE_DIR, medicine + ".mp3")

        if os.path.exists(audio_path):
            print("⏭️ Skipped:", medicine + ".mp3")
            continue

        json_path = os.path.join(TEXT_DIR, file)

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "counseling" in data:
                text = data["counseling"]
            elif "ai_counseling" in data:
                text = data["ai_counseling"]
            else:
                print("⚠️ No counseling text in:", file)
                continue

            text = text.strip()
            if not text:
                print("⚠️ Empty text:", file)
                continue

            generate_voice(text, audio_path)

        except Exception as e:
            print("❌ Failed:", file, e)
            time.sleep(3)


if __name__ == "__main__":
    main()
