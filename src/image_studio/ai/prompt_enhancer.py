"""Understand multilingual user prompts and prepare image-model instructions."""

from __future__ import annotations

import json
from typing import Protocol
from urllib.parse import urlsplit

import httpx

from .provider import ImageProviderError

_TASK_CONTEXT = {
    "generate": "Describe a new image based on the user's request.",
    "edit": (
        "Describe edits to an existing image. Preserve the existing scene and "
        "change only what the user requests."
    ),
    "variation": (
        "Describe a distinct variation of the source image while preserving its "
        "main subject and the user's requested direction."
    ),
}

_SYSTEM_PROMPT = """You prepare image-generation instructions from user descriptions.
The user may write in Vietnamese or another language. Understand the request
and return one concise English prompt for an image model. Preserve every named
subject, action, relationship, style, composition, color, material, lighting,
mood, and constraint. Do not invent or omit visual details. If the user asks for
specific words in the image, preserve those words exactly in their original
language and mark them as exact text. Return only the image prompt."""

MAX_PROMPT_RESPONSE_BYTES = 128 * 1024


class PromptEnhancer(Protocol):
    def enhance(self, prompt: str, operation: str) -> str: ...


class IdentityPromptEnhancer:
    """Pass prompts through when a caller injects a test image provider."""

    def enhance(self, prompt: str, operation: str) -> str:
        del operation
        return prompt


class OpenAICompatiblePromptEnhancer:
    """Use an OpenAI-compatible chat model to interpret and rewrite a prompt."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        model: str,
        timeout_seconds: float = 30,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds), transport=transport
        )

    def enhance(self, prompt: str, operation: str) -> str:
        task_context = _TASK_CONTEXT.get(operation)
        if task_context is None:
            raise ImageProviderError("This image operation is not supported.")
        if not self.base_url:
            raise ImageProviderError("Prompt language model URL is not configured.")
        try:
            hostname = urlsplit(self.base_url).hostname
        except ValueError as exc:
            raise ImageProviderError("Prompt language model URL is invalid.") from exc
        if not self.api_key and hostname == "api.openai.com":
            raise ImageProviderError(
                "Prompt language model credentials are not configured."
            )
        headers = {"Accept-Encoding": "identity"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"{_SYSTEM_PROMPT}\n\n{task_context}",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
                headers=headers,
            ) as response:
                if not response.is_success:
                    if response.status_code in {401, 403}:
                        message = (
                            "Prompt language model rejected its configured credentials."
                        )
                    elif response.status_code == 429:
                        message = (
                            "Prompt language model is rate limited. Try again later."
                        )
                    else:
                        message = (
                            "Prompt language model could not process this description."
                        )
                    raise ImageProviderError(message)
                content = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    if len(content) + len(chunk) > MAX_PROMPT_RESPONSE_BYTES:
                        raise ImageProviderError(
                            "Prompt language model response is too large."
                        )
                    content.extend(chunk)
        except httpx.TimeoutException as exc:
            raise ImageProviderError("Prompt language model timed out.") from exc
        except (httpx.HTTPError, httpx.InvalidURL) as exc:
            raise ImageProviderError("Prompt language model is unavailable.") from exc

        try:
            payload = json.loads(content)
            choices = payload["choices"]
            content = choices[0]["message"]["content"]
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ImageProviderError(
                "Prompt language model returned an invalid response."
            ) from exc
        rewritten = _message_text(content).strip()
        if not rewritten:
            raise ImageProviderError("Prompt language model returned an empty prompt.")
        return rewritten

    def close(self) -> None:
        self._client.close()


def _message_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part["text"]
            for part in content
            if isinstance(part, dict)
            and part.get("type") == "text"
            and isinstance(part.get("text"), str)
        )
    return ""
