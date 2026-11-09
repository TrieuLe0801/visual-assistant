"""Provider-independent image generation contract."""

from dataclasses import dataclass
from typing import Protocol


class ImageProviderError(Exception):
    """A provider call failed with a user-safe message."""


class UnsupportedImageOperation(ImageProviderError):
    """The configured provider cannot perform the requested operation."""


@dataclass(frozen=True)
class GeneratedImage:
    data: bytes
    mime_type: str


class ImageProvider(Protocol):
    """Provider-independent operations required by the application."""

    name: str
    model: str

    def generate(self, prompt: str) -> GeneratedImage: ...

    def edit(
        self, prompt: str, source: bytes, source_mime_type: str
    ) -> GeneratedImage: ...

    def variation(
        self, prompt: str, source: bytes, source_mime_type: str
    ) -> GeneratedImage: ...
