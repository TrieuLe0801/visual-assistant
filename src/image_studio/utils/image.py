"""Shared image format and safety checks."""

from __future__ import annotations

import warnings
from io import BytesIO

from PIL import Image

IMAGE_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


class ImageStorageError(Exception):
    """A generated image could not be safely written or read."""


def detect_image_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ImageStorageError("Image provider returned an unsupported image format.")


def validate_image(data: bytes, mime_type: str) -> str:
    if len(data) > MAX_IMAGE_BYTES:
        raise ImageStorageError("Generated image exceeds the 20 MiB storage limit.")
    actual_mime = detect_image_mime(data)
    if actual_mime != mime_type:
        raise ImageStorageError("Image provider returned inconsistent image data.")

    expected_format = {
        "image/png": "PNG",
        "image/jpeg": "JPEG",
        "image/webp": "WEBP",
    }[actual_mime]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if image.format != expected_format:
                    raise ImageStorageError(
                        "Image provider returned inconsistent image data."
                    )
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise ImageStorageError(
                        "Generated image exceeds the 40 megapixel safety limit."
                    )
                image.verify()
    except ImageStorageError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        raise ImageStorageError(
            "Image provider returned an invalid image file."
        ) from exc
    return actual_mime
