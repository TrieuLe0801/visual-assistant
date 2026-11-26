"""Persist and run image operations through a configured provider."""

from __future__ import annotations

from typing import Any, Literal

from langsmith import set_run_metadata, traceable

from ..database import Database, ImageRecord
from ..storage import LocalImageStorage
from ..utils.image import ImageStorageError
from .prompt_enhancer import IdentityPromptEnhancer, PromptEnhancer
from .provider import (
    GeneratedImage,
    ImageProvider,
    ImageProviderError,
    UnsupportedImageOperation,
)


class ImageOperationError(Exception):
    """A completed failure with a safe reason and message."""

    def __init__(
        self, reason: Literal["storage", "unsupported", "provider"], detail: str
    ) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class ImageService:
    def __init__(
        self,
        database: Database,
        storage: LocalImageStorage,
        provider: ImageProvider,
        prompt_enhancer: PromptEnhancer | None = None,
    ) -> None:
        self.database = database
        self.storage = storage
        self.provider = provider
        self.prompt_enhancer = prompt_enhancer or IdentityPromptEnhancer()

    @traceable(
        name="image_studio.operation",
        run_type="chain",
        process_inputs=lambda inputs: {
            "operation": inputs.get("operation"),
            "has_source": inputs.get("source") is not None,
        },
        process_outputs=lambda output: _trace_output(output),
    )
    def run(
        self,
        *,
        owner_id: str,
        prompt: str,
        operation: str,
        parent_id: str | None,
        source: tuple[bytes, str] | None = None,
    ) -> ImageRecord | None:
        record = self.database.create_image_operation(
            owner_id=owner_id,
            prompt=prompt,
            operation=operation,
            parent_id=parent_id,
            provider=self.provider.name,
            model=self.provider.model,
        )
        set_run_metadata(
            image_id=record.id, provider=record.provider, model=record.model
        )
        stored_path: str | None = None
        try:
            image_prompt = self.prompt_enhancer.enhance(prompt, operation)
            result = _invoke_provider(self.provider, operation, image_prompt, source)
            if not isinstance(result, GeneratedImage):
                raise ImageProviderError(
                    "Image provider returned an invalid image result."
                )
            stored = self.storage.save(owner_id, result.data, result.mime_type)
            stored_path = stored.relative_path
            self.database.mark_image_succeeded(
                record.id,
                file_path=stored.relative_path,
                mime_type=stored.mime_type,
                size_bytes=stored.size_bytes,
            )
            set_run_metadata(status="succeeded")
        except ImageStorageError as exc:
            self._fail(record.id, stored_path, str(exc))
            raise ImageOperationError("storage", str(exc)) from exc
        except (UnsupportedImageOperation, ImageProviderError) as exc:
            self._fail(record.id, stored_path, str(exc))
            reason = (
                "unsupported"
                if isinstance(exc, UnsupportedImageOperation)
                else "provider"
            )
            raise ImageOperationError(reason, str(exc)) from exc
        except OSError as exc:
            self._fail(record.id, stored_path, "Image storage is unavailable.")
            raise ImageOperationError(
                "storage", "Image storage is unavailable."
            ) from exc
        except Exception as exc:
            self._fail(record.id, stored_path, "Image operation failed.")
            raise ImageOperationError(
                "provider", "Image operation failed. Please try again."
            ) from exc
        return self.database.get_image(owner_id, record.id)

    def _fail(self, image_id: str, stored_path: str | None, error: str) -> None:
        if stored_path:
            self.storage.remove(stored_path)
        self.database.mark_image_failed(image_id, error)
        set_run_metadata(status="failed")


def _trace_output(output: Any) -> dict[str, str | None]:
    if not isinstance(output, ImageRecord):
        return {"status": "unknown"}
    return {
        "image_id": output.id,
        "status": output.status,
        "provider": output.provider,
        "model": output.model,
    }


@traceable(
    name="image_provider.operation",
    run_type="llm",
    process_inputs=lambda inputs: {
        "operation": inputs.get("operation"),
        "has_prompt": bool(inputs.get("prompt")),
        "has_source": inputs.get("source") is not None,
    },
    process_outputs=lambda output: {
        "status": "succeeded",
        "has_output": isinstance(output, GeneratedImage),
        **(
            {"usage_metadata": output.usage_metadata}
            if isinstance(output, GeneratedImage) and output.usage_metadata
            else {}
        ),
    },
)
def _invoke_provider(
    provider: ImageProvider,
    operation: str,
    prompt: str,
    source: tuple[bytes, str] | None,
) -> GeneratedImage:
    set_run_metadata(ls_provider=provider.name, ls_model_name=provider.model)
    if operation == "generate":
        return provider.generate(prompt)
    if operation not in {"edit", "variation"}:
        raise UnsupportedImageOperation("This image operation is not supported.")
    if source is None:
        raise ImageProviderError("Source image is unavailable.")
    method = getattr(provider, operation, None)
    if not callable(method):
        label = "editing" if operation == "edit" else "variations"
        raise UnsupportedImageOperation(
            f"Configured image provider does not support {label}."
        )
    return method(prompt, source[0], source[1])
