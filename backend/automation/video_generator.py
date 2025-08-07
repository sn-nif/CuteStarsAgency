import os
import requests
import tempfile
import uuid
from automation.captions import generate_caption
from automation.tts import generate_voiceover
from automation.pexels_api import get_broll_video
from automation.ffmpeg_tools import combine_audio_video
from automation.utils import upload_to_cloudinary

def generate_video_post(language):
    # Step 1: Generate caption
    caption = generate_caption(language)

    # Step 2: Generate voiceover (TTS)
    audio_path = generate_voiceover(caption, language)

    # Step 3: Get background video from Pexels
    video_path = get_broll_video(language)

    # Step 4: Combine voice + video
    output_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp4")
    combine_audio_video(video_path, audio_path, output_path)

    # Step 5: Upload to Cloudinary
    video_url, public_id = upload_to_cloudinary(output_path, resource_type="video")

    return {
        "post_id": str(uuid.uuid4()),
        "video_url": video_url,
        "caption": caption,
        "language": language,
        "cloudinary_id": public_id
    }
