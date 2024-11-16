import base64
import os
from uuid import uuid4

UPLOAD_DIR = "uploads"


def get_uuid4_filename_with_extention(filename: str) -> str:
    return str(uuid4()) + os.path.splitext(filename)[-1]


def get_image_from_base64(image: str) -> dict:
    prefix, contents = image.split(",", 1)
    datatype = prefix.split(";")[0].split(":")[1]
    if "image" in datatype:
        extention = prefix.split(";")[0].split(":image/")[1]
        return {
            "data": base64.b64decode(contents),
            "extention": extention,
        }
    if "application/octet-stream" in datatype:
        extention = ".jpeg"
        return {
            "data": base64.b64decode(contents),
            "extention": extention,
        }


def write_base64_file(file_base64: str) -> str:
    image_from_base64 = get_image_from_base64(file_base64)
    filename = get_uuid4_filename_with_extention(f"file.{image_from_base64['extention']}")
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        buffer.write(image_from_base64["data"])
    return filename
