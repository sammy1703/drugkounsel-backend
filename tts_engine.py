from openai import OpenAI
import os
import pathlib

client = OpenAI()

def generate_tts(text, language="english", filename="output", output_path: str | None = None):
    """
    Generate TTS audio and save to disk.

    - If `output_path` is provided, it will be used as the full path to write the MP3 file.
    - Otherwise the file will be written to `voices/{filename}_{language}.mp3` (backward compatible).
    """
    if output_path:
        out_path = pathlib.Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path = str(out_path)
    else:
        os.makedirs("voices", exist_ok=True)
        audio_path = f"voices/{filename}_{language}.mp3"

    # OpenAI TTS has a 4096 character limit
    safe_text = (text[:4000] + "...") if len(text) > 4000 else text

    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=safe_text
    ) as response:
        response.stream_to_file(audio_path)

    return audio_path
