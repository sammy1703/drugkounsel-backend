import os
import json
import time
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MASTER_PROMPT = """
You are a medical AI assistant for a patient education mobile app.

Generate patient counseling for the medicine: {medicine}.

Follow EXACTLY this structure:

1. What is this medicine?
(Write 2–3 short, simple sentences.)

2. Common side effects
(Write ONE concise sentence only.)

3. What to avoid when you are on this medicine
(Write ONE concise sentence only.)

4. When to report to the doctor
(Write ONE concise sentence only.)

Rules:
- Use very simple, patient-friendly language
- No abbreviations or shortcuts
- Do not mention dosage, frequency, or route
- Do not add extra sections
- Keep content accurate and safe

Return ONLY the counseling content.
"""

with open("failed_medicines.txt", "r", encoding="utf-8") as f:
    medicines = [line.strip() for line in f if line.strip()]

print(f"🔁 Retrying {len(medicines)} medicines")

OUTPUT_DIR = os.path.join(os.getcwd(), "counseling_json")
os.makedirs(OUTPUT_DIR, exist_ok=True)

for medicine in medicines:
    try:
        prompt = MASTER_PROMPT.format(medicine=medicine)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
            timeout=30
        )

        counseling_text = response.choices[0].message.content.strip()

        safe_name = (
            medicine.lower()
            .replace(" ", "_")
            .replace("+", "plus")
            .replace("/", "_")
            .replace("(", "")
            .replace(")", "")
        )

        with open(os.path.join(OUTPUT_DIR, f"{safe_name}.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "medicine": medicine,
                    "language": "en",
                    "ai_counseling": counseling_text
                },
                f,
                ensure_ascii=False,
                indent=2
            )

        print(f"✅ Generated: {medicine}")
        time.sleep(2)  # longer pause to avoid connection drop

    except Exception as e:
        print(f"❌ Still failed for {medicine}: {e}")
