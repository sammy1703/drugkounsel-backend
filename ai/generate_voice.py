from openai import OpenAI
import os
import json
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEXT_DIR = os.path.join(BASE_DIR, "counseling_json", "ur")
VOICE_DIR = os.path.join(BASE_DIR, "voice", "ur")

client = OpenAI(max_retries=2)
VOICE = "alloy"


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
    if not os.path.isdir(TEXT_DIR):
        print("❌ TEXT_DIR NOT FOUND")
        return

    os.makedirs(VOICE_DIR, exist_ok=True)

    for file in os.listdir(TEXT_DIR):
        if not file.endswith(".json"):
            continue

        json_path = os.path.join(TEXT_DIR, file)
        audio_path = os.path.join(VOICE_DIR, file.replace(".json", ".mp3"))

        if os.path.exists(audio_path):
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            text = data.get("ai_counseling") or data.get("counseling")
            if not text:
                continue

            generate_voice(text.strip(), audio_path)

        except Exception as e:
            print("❌ VOICE ERROR:", e)
            time.sleep(2)


if __name__ == "__main__":
    main()
