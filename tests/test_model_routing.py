"""Offline model selection and trace data boundary checks."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from langsmith import tracing_context
from langsmith.run_trees import RunTree
from PIL import Image

from image_studio.ai import GeneratedImage, ImageProviderError, build_provider
from image_studio.ai.model_router import LangChainImageProvider
from image_studio.ai.service import ImageOperationError, ImageService
from image_studio.config import ImageModelProfile, Settings, make_settings
from image_studio.database import Database
from image_studio.storage import LocalImageStorage


def _png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (1, 1), "red").save(buffer, format="PNG")
    return buffer.getvalue()


class _FakeModel:
    name = "fake"

    def __init__(self, model: str) -> None:
        self.model = model
        self.calls: list[tuple[str, str]] = []

    def generate(self, prompt: str) -> GeneratedImage:
        self.calls.append(("generate", prompt))
        return GeneratedImage(_png(), "image/png")

    def edit(self, prompt: str, source: bytes, source_mime_type: str) -> GeneratedImage:
        self.calls.append(("edit", prompt))
        return GeneratedImage(_png(), "image/png")

    def variation(
        self, prompt: str, source: bytes, source_mime_type: str
    ) -> GeneratedImage:
        self.calls.append(("variation", prompt))
        return GeneratedImage(_png(), "image/png")


class _FailModel(_FakeModel):
    def generate(self, prompt: str) -> GeneratedImage:
        raise ImageProviderError("Image provider is unavailable.")


def test_langchain_routes_each_operation_to_server_selected_model() -> None:
    first = _FakeModel("first")
    second = _FakeModel("second")
    router = LangChainImageProvider({"first": first, "second": second}, "first")
    switched = router.with_model("second")

    router.generate("one")
    switched.generate("two")
    switched.edit("three", _png(), "image/png")
    switched.variation("four", _png(), "image/png")

    assert first.calls == [("generate", "one")]
    assert second.calls == [
        ("generate", "two"),
        ("edit", "three"),
        ("variation", "four"),
    ]
    assert (router.model, switched.model) == ("first", "second")
    with pytest.raises(ValueError, match="not configured"):
        router.with_model("missing")


def test_catalog_selects_model_from_server_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "IMAGE_MODEL_CATALOG",
        json.dumps(
            {
                "cloud": {"provider": "openai", "model": "cloud-image"},
                "local": {"provider": "openai_compatible", "model": "local-image"},
            }
        ),
    )
    monkeypatch.setenv("IMAGE_ACTIVE_MODEL", "local")
    monkeypatch.setenv("IMAGE_API_BASE_URL", "http://127.0.0.1:8001/v1")
    settings = Settings.from_env()
    settings.validate()

    assert settings.active_model == "local"
    assert [(item.alias, item.model_name) for item in settings.model_catalog] == [
        ("cloud", "cloud-image"),
        ("local", "local-image"),
    ]
    assert settings.model_catalog[1].api_base_url == "http://127.0.0.1:8001/v1"


def test_invalid_catalog_and_active_model_fail_at_startup(tmp_path: Path) -> None:
    profile = ImageModelProfile(
        "cloud", "openai", "image-one", "https://api.openai.com/v1", None
    )
    settings = make_settings(
        database_path=tmp_path / "db.sqlite3",
        image_storage_path=tmp_path / "images",
        frontend_dist_path=tmp_path / "frontend",
        model_catalog=(profile,),
        active_model="missing",
    )
    with pytest.raises(ValueError, match="IMAGE_ACTIVE_MODEL"):
        settings.validate()


def test_factory_uses_active_catalog_profile(tmp_path: Path) -> None:
    cloud = ImageModelProfile(
        "cloud", "openai", "cloud-image", "https://api.openai.com/v1", None
    )
    local = ImageModelProfile(
        "local", "openai_compatible", "local-image", "http://127.0.0.1:8001/v1", None
    )
    settings = make_settings(
        database_path=tmp_path / "db.sqlite3",
        image_storage_path=tmp_path / "images",
        frontend_dist_path=tmp_path / "frontend",
        model_catalog=(cloud, local),
        active_model="local",
        provider_name="unused_legacy_value",
        model_name="",
    )
    settings.validate()
    router = build_provider(settings)
    try:
        assert (router.name, router.model) == ("openai_compatible", "local-image")
        assert router.with_model("cloud").model == "cloud-image"
    finally:
        router.close()


def test_settings_repr_omits_credentials(tmp_path: Path) -> None:
    profile = ImageModelProfile(
        "cloud", "openai", "cloud-image", "https://api.openai.com/v1", "profile-key"
    )
    settings = make_settings(
        database_path=tmp_path / "db.sqlite3",
        image_storage_path=tmp_path / "images",
        frontend_dist_path=tmp_path / "frontend",
        api_key="primary-key",
        session_secret="secret-long-enough-for-test",
        model_catalog=(profile,),
        active_model="cloud",
    )
    rendered = repr(settings)
    assert "primary-key" not in rendered
    assert "profile-key" not in rendered
    assert "secret-long-enough-for-test" not in rendered


def test_langsmith_trace_excludes_prompt_source_and_image_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[RunTree] = []
    original_end = RunTree.end

    def capture_end(run: RunTree, *args: object, **kwargs: object) -> None:
        original_end(run, *args, **kwargs)
        captured.append(run)

    monkeypatch.setattr(RunTree, "end", capture_end)
    settings = make_settings(
        database_path=tmp_path / "db.sqlite3",
        image_storage_path=tmp_path / "images",
        frontend_dist_path=tmp_path / "frontend",
    )
    database = Database(settings.database)
    database.initialize()
    user = database.create_user("test@example.com", "test-hash")
    storage = LocalImageStorage(settings.image_storage_path)
    storage.initialize()
    router = LangChainImageProvider({"only": _FakeModel("safe-model")}, "only")
    service = ImageService(database, storage, router)

    with tracing_context(enabled="local"):
        result = service.run(
            owner_id=user.id,
            prompt="private prompt marker",
            operation="generate",
            parent_id=None,
        )
        edited = service.run(
            owner_id=user.id,
            prompt="private edit marker",
            operation="edit",
            parent_id=result.id if result else None,
            source=(b"private source marker", "image/png"),
        )
        failing = ImageService(
            database,
            storage,
            LangChainImageProvider({"bad": _FailModel("bad-model")}, "bad"),
        )
        with pytest.raises(ImageOperationError, match="unavailable"):
            failing.run(
                owner_id=user.id,
                prompt="private failure marker",
                operation="generate",
                parent_id=None,
            )

    assert result is not None and result.status == "succeeded"
    assert edited is not None and edited.status == "succeeded"
    assert len(captured) == 3
    data = json.dumps(
        [{"inputs": trace.inputs, "outputs": trace.outputs} for trace in captured]
    )
    assert "private prompt marker" not in data
    assert "private edit marker" not in data
    assert "private source marker" not in data
    assert "private failure marker" not in data
    assert "test@example.com" not in data
    assert "safe-model" in data
    assert captured[0].inputs == {"operation": "generate", "has_source": False}
    assert captured[1].inputs == {"operation": "edit", "has_source": True}
    assert captured[2].extra["metadata"]["status"] == "failed"
