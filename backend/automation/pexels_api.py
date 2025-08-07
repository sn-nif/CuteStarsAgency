import os
import requests
import tempfile
import uuid

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# Keywords per language
VIDEO_KEYWORDS = {
    "en": "woman working home phone",
    "es": "mujer trabajando casa móvil",
    "pt": "mulher trabalhando casa celular",
    "ru": "девушка работает дома телефон",
    "sr": "devojka radi kod kuće telefon"
}

def get_broll_video(language):
    headers = {
        "Authorization": PEXELS_API_KEY
    }

    query = VIDEO_KEYWORDS.get(language, VIDEO_KEYWORDS["en"])
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=10&orientation=portrait"

    res = requests.get(url, headers=headers)
    res.raise_for_status()

    videos = res.json().get("videos", [])
    if not videos:
        raise Exception("No videos found for the query.")

    # Use first result, get smallest video file
    video_url = sorted(videos[0]["video_files"], key=lambda f: f["width"])[0]["link"]

    # Download the video
    video_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp4")
    r = requests.get(video_url)
    with open(video_path, "wb") as f:
        f.write(r.content)

    return video_path
