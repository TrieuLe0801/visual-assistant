"""Construct the configured image provider."""

from ..config import ImageModelProfile, Settings
from .model_router import LangChainImageProvider
from .openai_compatible import OpenAICompatibleProvider
from .provider import GeneratedImage, ImageProvider, ImageProviderError


class UnavailableImageProvider:
    """Delay missing provider configuration until image work is requested."""

    name: str

    def __init__(self, name: str, model: str, message: str) -> None:
        self.name = name
        self.model = model
        self._message = message

    def generate(self, prompt: str) -> GeneratedImage:
        raise ImageProviderError(self._message)

    def edit(self, prompt: str, source: bytes, source_mime_type: str) -> GeneratedImage:
        raise ImageProviderError(self._message)

    def variation(
        self, prompt: str, source: bytes, source_mime_type: str
    ) -> GeneratedImage:
        raise ImageProviderError(self._message)


def build_provider(settings: Settings) -> LangChainImageProvider:
    """Construct provider from validated Settings without exposing secrets."""
    profiles = settings.model_catalog or (
        ImageModelProfile(
            alias="default",
            provider_name=settings.provider_name,
            model_name=settings.model_name,
            api_base_url=settings.api_base_url,
            api_key=settings.api_key,
        ),
    )
    providers = {
        profile.alias: _build_profile(profile, settings) for profile in profiles
    }
    return LangChainImageProvider(providers, settings.active_model)


def _build_profile(profile: ImageModelProfile, settings: Settings) -> ImageProvider:
    provider_name = profile.provider_name
    model = profile.model_name
    api_key = profile.api_key
    base_url = profile.api_base_url
    if provider_name not in {"openai", "openai_compatible"}:
        raise ValueError("Unsupported IMAGE_PROVIDER value.")
    if not base_url:
        return UnavailableImageProvider(
            provider_name, model, "Image provider URL is not configured."
        )
    if provider_name == "openai" and not api_key:
        return UnavailableImageProvider(
            provider_name, model, "Image provider credentials are not configured."
        )
    return OpenAICompatibleProvider(
        base_url=base_url,
        api_key=str(api_key) if api_key else None,
        model=model,
        provider_name=provider_name,
        timeout_seconds=settings.provider_timeout_seconds,
    )
