import os
import random
import requests
import tempfile
import uuid

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# Keyword pool per language
KEYWORDS = {
    "en": ["women working", "remote work", "business woman", "girl laptop", "home office", "woman phone"],
    "es": ["mujer trabajando", "trabajo remoto", "oficina en casa", "chica laptop", "mujer teléfono"],
    "pt": ["mulher trabalhando", "trabalho remoto", "mulher laptop", "mulher telefone", "escritório em casa"],
    "ru": ["девушка работа", "работа из дома", "девушка с ноутбуком", "женщина телефон"],
    "sr": ["devojka radi", "rad od kuće", "žena laptop", "žena telefon"]
}

USED_IDS_FILE = "used_video_ids.txt"

def get_used_video_ids():
    if not os.path.exists(USED_IDS_FILE):
        return set()
    with open(USED_IDS_FILE, "r") as f:
        return set(f.read().splitlines())

def mark_video_id_used(video_id):
    with open(USED_IDS_FILE, "a") as f:
        f.write(f"{video_id}\n")

def get_broll_video(language="en"):
    query = random.choice(KEYWORDS.get(language, KEYWORDS["en"]))
    headers = {
        "Authorization": PEXELS_API_KEY
    }

    used_ids = get_used_video_ids()
    page = random.randint(1, 10)
    res = requests.get(
        f"https://api.pexels.com/videos/search?query={query}&per_page=10&page={page}",
        headers=headers
    )

    if res.status_code != 200:
        raise Exception("Failed to fetch from Pexels")

    videos = res.json().get("videos", [])
    random.shuffle(videos)

    for video in videos:
        video_id = str(video["id"])
        if video_id in used_ids:
            continue

        # Pick HD-quality version
        video_files = video.get("video_files", [])
        hd_versions = [f for f in video_files if f["quality"] == "hd"]

        if not hd_versions:
            continue

        download_url = hd_versions[0]["link"]
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp4")

        # Download the video
        video_data = requests.get(download_url)
        with open(temp_path, "wb") as f:
            f.write(video_data.content)

        mark_video_id_used(video_id)
        return temp_path

    raise Exception("No suitable HD videos found.")