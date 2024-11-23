import base64
import os
from uuid import uuid4

from kapi.db.db import supabase

UPLOAD_DIR = "uploads"

BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "image-uploads")

def get_local_file_path(filename):
    return os.path.join(UPLOAD_DIR, filename)

def get_file_from_bucket(filename, bucket=BUCKET_NAME):
    response = supabase.storage.from_(bucket).download(filename)
    file_path = get_local_file_path(filename)
    print('Download response from Supabase:', response)
    with open(file_path, "wb+") as f:
        f.write(response)

def get_mime_type_from_filename(filename):
    if filename.endswith(".png"):
        return "image/png"
    if filename.endswith(".jpeg"):
        return "image/jpeg"
    if filename.endswith(".jpg"):
        return "image/jpeg"
    raise ValueError("Unsupported file extension")

def upload_file_to_bucket(filename, bucket=BUCKET_NAME):
    print("Uploading file to bucket", filename)
    file_path = get_local_file_path(filename)
    with open(file_path, "rb") as f:
        response = supabase.storage.from_(bucket).upload(file=f, path=filename, file_options={
            "content-type": get_mime_type_from_filename(filename)
        })
        print('Upload response from Supabase:', response)

def get_uuid4_filename_with_extension(filename: str) -> str:
    return str(uuid4()) + os.path.splitext(filename)[-1]


def get_image_from_base64(image: str) -> dict:
    prefix, contents = image.split(",", 1)
    datatype = prefix.split(";")[0].split(":")[1]
    if "image" in datatype:
        extension = prefix.split(";")[0].split(":image/")[1]
        return {
            "data": base64.b64decode(contents),
            "extension": extension,
        }
    if "application/octet-stream" in datatype:
        extension = ".jpeg"
        return {
            "data": base64.b64decode(contents),
            "extension": extension,
        }


def write_base64_file(file_base64: str) -> str:
    image_from_base64 = get_image_from_base64(file_base64)
    filename = get_uuid4_filename_with_extension(f"file.{image_from_base64['extension']}")
    filepath = get_local_file_path(filename)
    with open(filepath, "wb") as buffer:
        buffer.write(image_from_base64["data"])
    return filename

