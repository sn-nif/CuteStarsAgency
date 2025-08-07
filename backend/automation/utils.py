import cloudinary
import cloudinary.uploader

def upload_to_cloudinary(file_path, resource_type="image"):
    try:
        response = cloudinary.uploader.upload(
            file_path,
            resource_type=resource_type,
            folder="cutestars_generated",
            use_filename=True,
            unique_filename=False,
            overwrite=True
        )
        return response["secure_url"], response["public_id"]
    except Exception as e:
        print(f"❌ Cloudinary upload error: {e}")
        raise