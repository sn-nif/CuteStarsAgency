import cloudinary
import cloudinary.uploader
import os

# Setup from .env
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_to_cloudinary(file_path, resource_type="video"):
    result = cloudinary.uploader.upload(
        file_path,
        resource_type=resource_type,
        folder="cutestars/videos",  # optional: folder for organization
        use_filename=True,
        unique_filename=True,
        overwrite=False
    )
    return result["secure_url"], result["public_id"]
