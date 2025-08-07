import openai
import os

# ✅ Set API key using new format
openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPTS = {
    "en": "Write a short (1-2 sentence) call-to-action script for a video encouraging women to work from home in a remote live streaming job. Keep it casual and motivating.",
    "es": "Escribe un guión corto (1-2 frases) para invitar a mujeres a trabajar desde casa como anfitrionas en vivo. Que sea inspirador y directo.",
    "pt": "Crie um pequeno roteiro (1-2 frases) incentivando mulheres a trabalhar de casa em lives. Seja empoderador e claro.",
    "ru": "Напиши короткий сценарий (1-2 предложения) для приглашения девушек работать из дома в онлайн трансляциях.",
    "sr": "Napiši kratak poziv (1-2 rečenice) devojkama da rade od kuće kao live hostese. Motivaciono i jednostavno."
}

def generate_caption(language):
    prompt = PROMPTS.get(language, PROMPTS["en"])

    # ✅ New correct API call
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=80
    )
    return response.choices[0].message.content.strip()
