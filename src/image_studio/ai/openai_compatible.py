"""OpenAI and OpenAI-compatible image API adapter."""

from __future__ import annotations

import base64
import binascii
import json

import httpx

from ..utils.image import IMAGE_EXTENSIONS, MAX_IMAGE_BYTES
from .provider import (
    GeneratedImage,
    ImageProviderError,
    UnsupportedImageOperation,
)

MAX_PROVIDER_RESPONSE_BYTES = 30 * 1024 * 1024


class OpenAICompatibleProvider:
    """Use OpenAI-style `/images/*` endpoints and base64 image responses.

    The configured OpenAI-compatible service must accept image generation JSON
    at `/images/generations`, multipart image edits at `/images/edits`, and
    return `data[0].b64_json` (or a base64 data URL). Variation calls use the
    edits endpoint with a variation prompt. The adapter does not follow image
    URLs from provider output, which avoids server-side requests to untrusted
    destinations.
    """

    name = "openai"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        model: str,
        provider_name: str = "openai",
        timeout_seconds: float = 180,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = provider_name
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds), transport=transport
        )

    def generate(self, prompt: str) -> GeneratedImage:
        response = self._post_json(
            "/images/generations",
            {"model": self.model, "prompt": prompt, "output_format": "png"},
        )
        return _image_from_response(response)

    def edit(self, prompt: str, source: bytes, source_mime_type: str) -> GeneratedImage:
        response = self._post_edit(prompt, source, source_mime_type)
        return _image_from_response(response)

    def variation(
        self, prompt: str, source: bytes, source_mime_type: str
    ) -> GeneratedImage:
        """Create a variation through image edit endpoint.

        Current GPT Image models do not provide a model-supported legacy
        variations endpoint. OpenAI image edits support a source image and
        prompt, so this adapter expresses a variation as an edit operation.
        """
        instruction = "Create a distinct variation of the source image."
        if prompt.strip():
            instruction = f"{instruction} Direction: {prompt.strip()}"
        response = self._post_edit(instruction, source, source_mime_type)
        return _image_from_response(response)

    def close(self) -> None:
        self._client.close()

    def _post_json(self, path: str, payload: dict[str, str]) -> dict[str, object]:
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}{path}",
                json=payload,
                headers=self._headers(),
            ) as response:
                return self._read_response(response)
        except httpx.TimeoutException as exc:
            raise ImageProviderError("Image provider timed out.") from exc
        except httpx.HTTPError as exc:
            raise ImageProviderError("Image provider is unavailable.") from exc

    def _post_edit(
        self, prompt: str, source: bytes, source_mime_type: str
    ) -> dict[str, object]:
        extension = IMAGE_EXTENSIONS.get(source_mime_type)
        if extension is None:
            raise UnsupportedImageOperation(
                "The source image format is not supported for editing."
            )
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/images/edits",
                data={"model": self.model, "prompt": prompt, "output_format": "png"},
                files={"image": (f"source.{extension}", source, source_mime_type)},
                headers=self._headers(),
            ) as response:
                if response.status_code in {404, 405, 501}:
                    raise UnsupportedImageOperation(
                        "Configured image provider does not support image edits."
                    )
                return self._read_response(response)
        except httpx.TimeoutException as exc:
            raise ImageProviderError("Image provider timed out.") from exc
        except httpx.HTTPError as exc:
            raise ImageProviderError("Image provider is unavailable.") from exc

    def _headers(self) -> dict[str, str]:
        headers = {"Accept-Encoding": "identity"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def _read_response(response: httpx.Response) -> dict[str, object]:
        if not response.is_success:
            status = response.status_code
            if status in {400, 422}:
                message = "Image provider rejected this prompt or source image."
            elif status in {401, 403}:
                message = "Image provider rejected its configured credentials."
            elif status == 429:
                message = "Image provider is rate limited. Try again later."
            elif status >= 500:
                message = "Image provider is temporarily unavailable."
            else:
                message = "Image provider could not complete the request."
            raise ImageProviderError(message)
        content = bytearray()
        for chunk in response.iter_bytes(chunk_size=65536):
            if len(content) + len(chunk) > MAX_PROVIDER_RESPONSE_BYTES:
                raise ImageProviderError("Image provider response is too large.")
            content.extend(chunk)
        try:
            payload = json.loads(content)
        except ValueError as exc:
            raise ImageProviderError("Image provider returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise ImageProviderError("Image provider returned an invalid response.")
        return payload


def _image_from_response(payload: dict[str, object]) -> GeneratedImage:
    images = payload.get("data")
    if not isinstance(images, list) or not images or not isinstance(images[0], dict):
        raise ImageProviderError("Image provider returned no image data.")
    encoded = images[0].get("b64_json")
    if not isinstance(encoded, str) or not encoded:
        raise ImageProviderError(
            "Image provider response must contain base64 image data."
        )
    mime_type = "image/png"
    if encoded.startswith("data:"):
        header, separator, encoded = encoded.partition(",")
        if not separator or ";base64" not in header:
            raise ImageProviderError("Image provider returned an invalid data URL.")
        mime_type = header[5:].split(";", maxsplit=1)[0]
    max_encoded_length = 4 * ((MAX_IMAGE_BYTES + 2) // 3)
    if len(encoded) > max_encoded_length:
        raise ImageProviderError(
            "Image provider returned an image over the 20 MiB limit."
        )
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ImageProviderError(
            "Image provider returned invalid base64 image data."
        ) from exc
    return GeneratedImage(data=data, mime_type=mime_type)
