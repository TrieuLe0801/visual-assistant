"""Server-selected image model routing through LangChain runnables."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from langchain_core.runnables import ConfigurableField, RunnableLambda
from langchain_core.runnables.configurable import RunnableConfigurableAlternatives
from langsmith import tracing_context

from .provider import (
    GeneratedImage,
    ImageProvider,
    ImageProviderError,
    UnsupportedImageOperation,
)


@dataclass(frozen=True)
class ImageRequest:
    operation: str
    prompt: str
    source: bytes | None = None
    source_mime_type: str | None = None


class LangChainImageProvider:
    """Select a configured provider/model without exposing selection to API users.

    LangChain receives prompt and image bytes in memory. Its automatic tracing
    is disabled here; ImageService records a sanitized LangSmith span instead.
    """

    def __init__(
        self, providers: Mapping[str, ImageProvider], active_model: str
    ) -> None:
        if not providers or active_model not in providers:
            raise ValueError("Active image model is not configured.")
        self._providers = dict(providers)
        self.active_model = active_model
        selected = self._providers[active_model]
        self.name = selected.name
        self.model = selected.model
        first_alias = next(iter(self._providers))
        runnables = {
            alias: RunnableLambda(
                lambda request, provider=provider: _invoke(provider, request),
                name=f"image_model_{alias}",
            ).with_config()
            for alias, provider in self._providers.items()
        }
        self._router = RunnableConfigurableAlternatives(
            which=ConfigurableField(id="image_model"),
            default=runnables.pop(first_alias),
            default_key=first_alias,
            alternatives=runnables,
            prefix_keys=False,
        )

    def with_model(self, alias: str) -> LangChainImageProvider:
        """Select another server-configured model for a new service instance."""
        return LangChainImageProvider(self._providers, alias)

    def generate(self, prompt: str) -> GeneratedImage:
        return self._run(ImageRequest("generate", prompt))

    def edit(self, prompt: str, source: bytes, source_mime_type: str) -> GeneratedImage:
        return self._run(ImageRequest("edit", prompt, source, source_mime_type))

    def variation(
        self, prompt: str, source: bytes, source_mime_type: str
    ) -> GeneratedImage:
        return self._run(ImageRequest("variation", prompt, source, source_mime_type))

    def _run(self, request: ImageRequest) -> GeneratedImage:
        # Runnable traces would include prompts, source bytes and result bytes.
        with tracing_context(enabled=False):
            return self._router.invoke(
                request, config={"configurable": {"image_model": self.active_model}}
            )

    def close(self) -> None:
        for provider in self._providers.values():
            close = getattr(provider, "close", None)
            if callable(close):
                close()


def _invoke(provider: ImageProvider, request: ImageRequest) -> GeneratedImage:
    if request.operation == "generate":
        return provider.generate(request.prompt)
    if request.source is None or request.source_mime_type is None:
        raise ImageProviderError("Source image is unavailable.")
    if request.operation == "edit":
        return provider.edit(request.prompt, request.source, request.source_mime_type)
    if request.operation == "variation":
        return provider.variation(
            request.prompt, request.source, request.source_mime_type
        )
    raise UnsupportedImageOperation("This image operation is not supported.")
