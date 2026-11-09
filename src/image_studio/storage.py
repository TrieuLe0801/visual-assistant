"""Local, private image file storage."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from .utils.image import IMAGE_EXTENSIONS, ImageStorageError, validate_image


@dataclass(frozen=True)
class StoredImage:
    relative_path: str
    mime_type: str
    size_bytes: int


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
        extension = IMAGE_EXTENSIONS[actual_mime]
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
