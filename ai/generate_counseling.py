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
    """
    Generates counseling information for a medicine using OpenAI.
    """
    prompt = f"""
    You are an experienced clinical pharmacist.
    Generate INDIVIDUALIZED, MEDICINE-SPECIFIC patient counseling for: "{medicine}".
    Language: "{lang}"

    STRICT FORMATTING RULE:
    The frontend splits text by "\\nNumber. ".
    You MUST output the text in this EXACT structure:

    1. WHAT IS THIS MEDICINE FOR
    (Put content on this new line. Do NOT use a colon after the header.)

    2. HOW TO TAKE
    (Put content on this new line.)

    3. IMPORTANT WARNINGS
    (Put content on this new line.)

    4. COMMON SIDE EFFECTS
    (Put content on this new line.)

    5. GENERAL INSTRUCTIONS
    (Put content on this new line.)

    6. DRUG FOOD INTERACTION
    (Put content on this new line. If there are specific foods to avoid due to high interaction potency, list them clearly. Use professional language to advise avoiding these foods during the medication course.)

    CONTENT RULES:
    - Use simple Layman terms.
    - Be specific to "{medicine}".
    - Do NOT include markdown bold (**).
    - Ensure there is a newline between the header and the content.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant that outputs only JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        content = response.choices[0].message.content
        try:
             with open("debug_log.txt", "a") as f:
                 f.write(f"RAW CONTENT: {content}\n")
        except:
             pass
        data = json.loads(content)
        
        if "ai_counseling" in data:
            return data["ai_counseling"]
            
        # Fallback: Reconstruct string from keys if model returned structured JSON
        constructed_text = []
        for key, value in data.items():
            header = key.strip()
            # Ensure header starts with a number
            if header[0].isdigit():
                constructed_text.append(f"{header}\n{value}")
                
        if constructed_text:
            return "\n\n".join(constructed_text)
            
        return None

    except Exception as e:
        print(f"❌ OPENAI GENERATION ERROR: {e}")
        try:
            with open("debug_log.txt", "a") as f:
                f.write(f"OPENAI ERROR: {str(e)}\n")
        except:
            pass
        return None


def generate_interactions_section(target: str, existing: list, lang: str):
    """
    Check for drug-drug interactions between target and existing list.
    Returns a string for Section 7.
    """
    if not existing:
        return [
            {
                "drug_pair": "None",
                "severity": "None",
                "description": "No other medicines provided for interaction check."
            }
        ]

    existing_str = ", ".join(existing)
    

    prompt = f"""
    You are an expert clinical pharmacist.
    Check for DRUG-DRUG INTERACTIONS between "{target}" and these existing patient medications: "{existing_str}".
    Language: "{lang}"

    OUTPUT FORMAT:
    You must output a JSON object with a key "interactions".
    The value should be a list of objects, each containing:
    - "drug_pair": "Name of Drug A + Name of Drug B" (or "General" if applies to all)
    - "severity": "High", "Moderate", "Low", or "None"
    - "description": "Professional explanation of the interaction, TRANSLATED into {lang}."

    Example:
    {{
        "interactions": [
            {{
                "drug_pair": "Aspirin + Warfarin",
                "severity": "High",
                "description": "(Explanation in {lang}) Increased risk of bleeding..."
            }}
        ]
    }}

    If no interactions are found, return:
    {{
        "interactions": [
            {{
                "drug_pair": "{target} + Others",
                "severity": "None",
                "description": "No significant drug-drug interactions found (Translated to {lang})."
            }}
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant that outputs only JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3, 
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return data.get("interactions", [])
    except Exception as e:
        print(f"❌ INTERACTION CHECK ERROR: {e}")
        return []

def generate_and_store_counseling(medicine: str, lang: str, existing_drugs: list = None):
    safe_name = normalize_name(medicine)

    # Ensure language directory exists
    lang_dir = os.path.join(BASE_DIR, "counseling_json", lang)
    os.makedirs(lang_dir, exist_ok=True)

    file_path = os.path.join(lang_dir, f"{safe_name}.json")

    base_text = None

    # 1. CHECK LOCAL FILE FOR BASE COUNSELING (Sections 1-6)
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"✅ Found local data for {medicine} ({lang})")
                base_text = data.get("ai_counseling")
        except Exception as e:
            print("❌ FILE READ ERROR:", e)

    # 2. GENERATE BASE DYNAMICALLY IF NOT FOUND
    if not base_text:
        print(f"⚠️ {medicine} ({lang}) not found locally. Generating via AI...")
        base_text = generate_counseling_from_ai(medicine, lang) # Sections 1-6

        if base_text:
            # Save base content to file
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"ai_counseling": base_text}, f, ensure_ascii=False, indent=2)
                print(f"💾 Saved generated counseling to {file_path}")
            except Exception as e:
                print(f"❌ FILE SAVE ERROR: {e}")

    # 3. GENERATE DYNAMIC INTERACTION SECTION (Section 7)
    interaction_text = generate_interactions_section(medicine, existing_drugs, lang)

    # 4. GENERATE TTS IF NOT EXISTS
    # Voice should be in public/voices/<lang>/<medicine>.mp3
    # Go up one level from backend/ai/ to backend/ then to public/
    public_voices_path = os.path.join(os.path.dirname(BASE_DIR), "..", "public", "voices", lang)
    os.makedirs(public_voices_path, exist_ok=True)
    audio_file_name = f"{safe_name}.mp3"
    audio_full_path = os.path.join(public_voices_path, audio_file_name)

    if not os.path.exists(audio_full_path) and base_text:
        print(f"🎤 Generating voice for {medicine} in {lang}...")
        try:
            generate_tts(base_text, language=lang, output_path=audio_full_path)
            print(f"🎵 Voice saved to {audio_full_path}")
        except Exception as e:
            print(f"❌ TTS GENERATION ERROR: {e}")

    # 5. RETURN SEPARATELY
    return {
        "text": base_text,
        "interactions": interaction_text,
        "audio": f"/voices/{lang}/{audio_file_name}" if os.path.exists(audio_full_path) else None
    }
