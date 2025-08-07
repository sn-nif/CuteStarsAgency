import subprocess

def combine_audio_video(video_path, audio_path, output_path):
    command = [
        "ffmpeg",
        "-y",  # Overwrite output file if exists
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",  # Copy video stream without re-encoding
        "-c:a", "aac",   # Encode audio to AAC
        "-shortest",     # Trim output to shortest input (audio or video)
        output_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
