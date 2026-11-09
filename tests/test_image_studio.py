"""Deterministic tests for image studio API contracts and isolation."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from image_studio.ai import (
    GeneratedImage,
    ImageProviderError,
    OpenAICompatibleProvider,
    UnsupportedImageOperation,
)
from image_studio.app import create_app
from image_studio.config import make_settings
from image_studio.storage import LocalImageStorage, StoredImage
from image_studio.utils.image import MAX_IMAGE_BYTES, ImageStorageError


def _one_pixel_png() -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", (1, 1), (18, 52, 86, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


PNG_BYTES = _one_pixel_png()


class FakeProvider:
    name = "fake"
    model = "fixture-image-model"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, bytes | None]] = []
        self.fail = False
        self.unsupported_variation = False
        self.image_data = PNG_BYTES

    def generate(self, prompt: str) -> GeneratedImage:
        self.calls.append(("generate", prompt, None))
        return self._result()

    def edit(self, prompt: str, source: bytes, source_mime_type: str) -> GeneratedImage:
        self.calls.append(("edit", prompt, source))
        return self._result()

    def variation(
        self, prompt: str, source: bytes, source_mime_type: str
    ) -> GeneratedImage:
        self.calls.append(("variation", prompt, source))
        if self.unsupported_variation:
            raise UnsupportedImageOperation(
                "Configured image provider does not support variations."
            )
        return self._result()

    def _result(self) -> GeneratedImage:
        if self.fail:
            raise ImageProviderError("Image provider is temporarily unavailable.")
        return GeneratedImage(self.image_data, "image/png")


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def client(tmp_path: Path, fake_provider: FakeProvider) -> TestClient:
    settings = make_settings(
        database_path=tmp_path / "images.sqlite3",
        image_storage_path=tmp_path / "image-files",
        frontend_dist_path=tmp_path / "frontend-dist",
    )
    app = create_app(settings=settings, provider=fake_provider)
    with TestClient(app) as test_client:
        yield test_client


def test_frontend_build_files_and_client_routes_are_served(
    tmp_path: Path,
) -> None:
    frontend = tmp_path / "frontend-dist"
    assets = frontend / "assets"
    assets.mkdir(parents=True)
    (frontend / "index.html").write_text("<main>Studio</main>", encoding="utf-8")
    (assets / "app.js").write_text("window.ready = true", encoding="utf-8")
    settings = make_settings(
        database_path=tmp_path / "site.sqlite3",
        image_storage_path=tmp_path / "site-images",
        frontend_dist_path=frontend,
    )

    with TestClient(create_app(settings=settings, provider=FakeProvider())) as client:
        assert client.get("/").text == "<main>Studio</main>"
        assert client.get("/images/example").text == "<main>Studio</main>"
        assert client.get("/assets/app.js").text == "window.ready = true"
        assert client.get("/api/missing").status_code == 404


def register(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register", json={"email": email, "password": "strong-pass-123"}
    )
    assert response.status_code == 201
    assert "httponly" in response.headers["set-cookie"].lower()
    return response.json()


def test_register_login_logout_and_password_protection(client: TestClient) -> None:
    account = register(client, "User@Example.com")
    assert account["email"] == "user@example.com"
    assert client.get("/api/auth/me").json()["id"] == account["id"]

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401

    failed = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    assert failed.status_code == 401

    logged_in = client.post(
        "/api/auth/login",
        json={"email": "USER@example.com", "password": "strong-pass-123"},
    )
    assert logged_in.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_generate_persists_prompt_file_and_owner_scope(
    client: TestClient, fake_provider: FakeProvider
) -> None:
    register(client, "owner@example.com")
    generated = client.post(
        "/api/images/generate", json={"prompt": "  A blue house at dusk  "}
    )
    assert generated.status_code == 201
    record = generated.json()
    assert record["prompt"] == "A blue house at dusk"
    assert record["operation"] == "generate"
    assert record["status"] == "succeeded"
    assert record["parent_id"] is None
    assert record["file_url"] == f"/api/images/{record['id']}/file"
    assert fake_provider.calls == [("generate", "A blue house at dusk", None)]

    file_response = client.get(record["file_url"])
    assert file_response.status_code == 200
    assert file_response.headers["content-type"] == "image/png"
    assert file_response.content == PNG_BYTES
    assert client.get("/api/images").json()[0]["prompt"] == "A blue house at dusk"


def test_edit_and_variation_keep_source_relationship_and_prompt(
    client: TestClient, fake_provider: FakeProvider
) -> None:
    register(client, "creator@example.com")
    original = client.post("/api/images/generate", json={"prompt": "A mountain"}).json()

    edited = client.post(
        f"/api/images/{original['id']}/edit",
        json={"prompt": "Add a red moon"},
    )
    assert edited.status_code == 201
    assert edited.json()["parent_id"] == original["id"]
    assert edited.json()["prompt"] == "Add a red moon"
    assert fake_provider.calls[-1] == ("edit", "Add a red moon", PNG_BYTES)

    variation = client.post(f"/api/images/{original['id']}/variations", json={})
    assert variation.status_code == 201
    assert variation.json()["parent_id"] == original["id"]
    assert variation.json()["operation"] == "variation"
    assert variation.json()["prompt"] == "Tạo một biến thể khác biệt từ ảnh gốc."
    assert fake_provider.calls[-1][0] == "variation"


def test_other_user_cannot_list_read_edit_or_download_images(
    client: TestClient,
) -> None:
    register(client, "first@example.com")
    image = client.post("/api/images/generate", json={"prompt": "Private"}).json()
    client.post("/api/auth/logout")
    register(client, "second@example.com")

    assert client.get("/api/images").json() == []
    assert client.get(f"/api/images/{image['id']}").status_code == 404
    assert client.get(f"/api/images/{image['id']}/file").status_code == 404
    assert (
        client.post(
            f"/api/images/{image['id']}/edit", json={"prompt": "Change this"}
        ).status_code
        == 404
    )


def test_provider_error_is_recorded_as_failure_not_success(
    client: TestClient, fake_provider: FakeProvider
) -> None:
    register(client, "failure@example.com")
    fake_provider.fail = True
    response = client.post("/api/images/generate", json={"prompt": "Fail safely"})
    assert response.status_code == 502
    assert response.json()["detail"] == "Image provider is temporarily unavailable."
    records = client.get("/api/images").json()
    assert records[0]["status"] == "failed"
    assert records[0]["file_url"] is None
    assert records[0]["error"] == response.json()["detail"]


def test_oversized_provider_image_is_rejected_and_recorded_as_failure(
    client: TestClient, fake_provider: FakeProvider
) -> None:
    register(client, "large-image@example.com")
    fake_provider.image_data = PNG_BYTES + b"x" * MAX_IMAGE_BYTES

    response = client.post(
        "/api/images/generate", json={"prompt": "A very large generated image"}
    )

    assert response.status_code == 500
    assert "20 MiB" in response.json()["detail"]
    records = client.get("/api/images").json()
    assert records[0]["status"] == "failed"
    assert records[0]["file_url"] is None
    assert list(client.app.state.storage.root.rglob("*.png")) == []


def test_invalid_provider_image_is_rejected(
    client: TestClient, fake_provider: FakeProvider
):
    register(client, "invalid-image@example.com")
    fake_provider.image_data = b"\x89PNG\r\n\x1a\ntruncated"

    response = client.post(
        "/api/images/generate", json={"prompt": "A malformed result"}
    )

    assert response.status_code == 500
    assert "invalid image file" in response.json()["detail"]
    record = client.get("/api/images").json()[0]
    assert record["status"] == "failed"
    assert record["file_url"] is None


def test_storage_write_failure_is_recorded_and_not_returned_as_success(
    tmp_path: Path, fake_provider: FakeProvider
) -> None:
    class FailingStorage(LocalImageStorage):
        def save(self, owner_id: str, data: bytes, mime_type: str) -> StoredImage:
            raise ImageStorageError("Image storage is unavailable.")

    storage = FailingStorage(tmp_path / "write-failure-images")
    settings = make_settings(
        database_path=tmp_path / "write-failure.sqlite3",
        image_storage_path=storage.root,
        frontend_dist_path=tmp_path / "frontend-dist",
    )
    app = create_app(settings=settings, provider=fake_provider, storage=storage)
    with TestClient(app) as client:
        register(client, "storage-failure@example.com")
        response = client.post(
            "/api/images/generate", json={"prompt": "A stored image"}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Image storage is unavailable."
        records = client.get("/api/images").json()
        assert len(records) == 1
        assert records[0]["status"] == "failed"
        assert records[0]["file_url"] is None
        assert fake_provider.calls == [("generate", "A stored image", None)]


def test_unsupported_operation_is_explicit_and_recorded_as_failure(
    client: TestClient, fake_provider: FakeProvider
) -> None:
    register(client, "unsupported@example.com")
    original = client.post("/api/images/generate", json={"prompt": "A river"}).json()
    fake_provider.unsupported_variation = True

    response = client.post(f"/api/images/{original['id']}/variations", json={})

    assert response.status_code == 501
    assert "does not support variations" in response.json()["detail"]
    records = client.get("/api/images").json()
    failed_variation = next(
        record for record in records if record["operation"] == "variation"
    )
    assert failed_variation["status"] == "failed"


def test_prompt_and_image_survive_app_restart_and_login(tmp_path: Path) -> None:
    settings = make_settings(
        database_path=tmp_path / "persistent.sqlite3",
        image_storage_path=tmp_path / "persistent-images",
        frontend_dist_path=tmp_path / "frontend-dist",
    )
    first_app = create_app(settings=settings, provider=FakeProvider())
    with TestClient(first_app) as first_client:
        register(first_client, "restart@example.com")
        created = first_client.post(
            "/api/images/generate", json={"prompt": "A paper crane"}
        ).json()
        assert first_client.get(created["file_url"]).content == PNG_BYTES
        assert first_client.post("/api/auth/logout").status_code == 204

    second_app = create_app(settings=settings, provider=FakeProvider())
    with TestClient(second_app) as second_client:
        login = second_client.post(
            "/api/auth/login",
            json={"email": "restart@example.com", "password": "strong-pass-123"},
        )
        assert login.status_code == 200
        saved = second_client.get("/api/images").json()
        assert saved[0]["prompt"] == "A paper crane"
        assert second_client.get(saved[0]["file_url"]).content == PNG_BYTES


def test_prompt_validation_blocks_blank_and_oversized_requests(
    client: TestClient,
) -> None:
    register(client, "validation@example.com")
    assert client.post("/api/images/generate", json={"prompt": "  "}).status_code == 422
    assert (
        client.post("/api/images/generate", json={"prompt": "x" * 4001}).status_code
        == 422
    )


def test_registration_rejects_passwords_outside_ui_limits(client: TestClient) -> None:
    short = client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "short123"},
    )
    long = client.post(
        "/api/auth/register",
        json={"email": "long@example.com", "password": "p" * 129},
    )

    assert short.status_code == 422
    assert long.status_code == 422
    assert (
        short.json()["detail"] == "Password must contain between 10 and 128 characters."
    )
    assert long.json()["detail"] == short.json()["detail"]


def test_openai_compatible_adapter_uses_configured_routes_and_base64_only() -> None:
    requests: list[httpx.Request] = []
    request_bodies: list[bytes] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        request_bodies.append(request.read())
        return httpx.Response(
            200,
            json={"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode()}]},
            request=request,
        )

    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key="test-secret",
        model="test-model",
        provider_name="openai_compatible",
        transport=httpx.MockTransport(respond),
    )
    try:
        assert provider.generate("A lantern").data == PNG_BYTES
        assert provider.edit("Make it blue", PNG_BYTES, "image/png").data == PNG_BYTES
        assert (
            provider.variation("Use winter colors", PNG_BYTES, "image/png").data
            == PNG_BYTES
        )
    finally:
        provider.close()

    assert [request.url.path for request in requests] == [
        "/v1/images/generations",
        "/v1/images/edits",
        "/v1/images/edits",
    ]
    assert all(
        request.headers["authorization"] == "Bearer test-secret" for request in requests
    )
    assert b"Make it blue" in request_bodies[1]
    assert b"Use winter colors" in request_bodies[2]


def test_adapter_maps_unsupported_edit_endpoint_to_clear_capability_error() -> None:
    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key=None,
        model="test-model",
        provider_name="openai_compatible",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(501, request=request)
        ),
    )
    try:
        with pytest.raises(UnsupportedImageOperation, match="does not support"):
            provider.variation("Make a variation", PNG_BYTES, "image/png")
    finally:
        provider.close()
