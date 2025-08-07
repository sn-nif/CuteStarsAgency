import os
import uuid
import tempfile
import requests

# Female voice mapping per language (customize if needed)
VOICE_MAP = {
    "en": "Rachel",      # English female
    "es": "Paola",       # Spanish female
    "pt": "Camila",      # Portuguese female
    "ru": "Tatyana",     # Russian female
    "sr": "Rachel"       # Serbian fallback (no native, use English female)
}

def generate_voiceover(text, language):
    ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
    voice = VOICE_MAP.get(language, "Rachel")  # fallback to English female

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.85
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"ElevenLabs TTS failed: {response.status_code}, {response.text}")

    audio_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return audio_path