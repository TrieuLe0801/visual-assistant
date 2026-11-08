"""Local, private image file storage."""

from __future__ import annotations

import os
import uuid
import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


class ImageStorageError(Exception):
    """A generated image could not be safely written or read."""


@dataclass(frozen=True)
class StoredImage:
    relative_path: str
    mime_type: str
    size_bytes: int


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


class LocalImageStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def initialize(self) -> None:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ImageStorageError("Image storage is unavailable.") from exc

    def save(self, owner_id: str, data: bytes, mime_type: str) -> StoredImage:
        actual_mime = validate_image(data, mime_type)
        extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[
            actual_mime
        ]
        relative_path = Path(owner_id) / f"{uuid.uuid4().hex}.{extension}"
        target = (self.root / relative_path).resolve()
        if self.root not in target.parents:
            raise ImageStorageError("Image storage path is invalid.")
        temporary = target.with_name(f".{target.name}.tmp")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with temporary.open("xb") as image_file:
                image_file.write(data)
                image_file.flush()
                os.fsync(image_file.fileno())
            temporary.replace(target)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise ImageStorageError("Image storage is unavailable.") from exc
        return StoredImage(str(relative_path), actual_mime, len(data))

    def resolve(self, relative_path: str) -> Path:
        target = (self.root / relative_path).resolve()
        if self.root not in target.parents or not target.is_file():
            raise ImageStorageError("Image file is unavailable.")
        return target

    def remove(self, relative_path: str) -> None:
        try:
            self.resolve(relative_path).unlink(missing_ok=True)
        except (OSError, ImageStorageError):
            pass
