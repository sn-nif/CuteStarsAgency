import subprocess
import os

def combine_audio_video(video_path, audio_path, output_path):
    try:
        # Stretch or trim video to match audio length
        temp_video = output_path.replace(".mp4", "_resized.mp4")

        # Get audio duration
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        audio_duration = float(result.stdout.strip())

        # Trim or loop video to match audio duration
        subprocess.run([
            "ffmpeg",
            "-y",  # overwrite output
            "-stream_loop", "-1",  # infinite loop
            "-i", video_path,
            "-t", str(audio_duration),
            "-c", "copy",
            temp_video
        ], check=True)

        # Combine video + audio
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", temp_video,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ], check=True)

        # Cleanup temp
        if os.path.exists(temp_video):
            os.remove(temp_video)

    except Exception as e:
        print(f"❌ FFmpeg error: {e}")
        raise