from gtts import gTTS
import tempfile
import uuid
import os

# Maps language codes to gTTS language codes
TTS_LANG_MAP = {
    "en": "en",
    "es": "es",
    "pt": "pt",
    "ru": "ru",
    "sr": "sr"
}

def generate_voiceover(text, language):
    tts_lang = TTS_LANG_MAP.get(language, "en")
    tts = gTTS(text=text, lang=tts_lang)
    
    audio_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
    tts.save(audio_path)
    
    return audio_path
