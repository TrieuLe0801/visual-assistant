"""Deterministic tests for image studio API contracts and isolation."""

from __future__ import annotations

import base64
import importlib
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


def _one_pixel_png(color: tuple[int, int, int, int] = (18, 52, 86, 255)) -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", (1, 1), color).save(buffer, format="PNG")
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
    assert client.get("/api/auth/me").headers["cache-control"] == "no-store"

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


def test_logout_revokes_captured_cookie_across_restart_and_keeps_other_session(
    tmp_path: Path,
) -> None:
    settings = make_settings(
        database_path=tmp_path / "revocation.sqlite3",
        image_storage_path=tmp_path / "revocation-images",
        frontend_dist_path=tmp_path / "frontend-dist",
    )
    app = create_app(settings=settings, provider=FakeProvider())
    with TestClient(app) as first_client:
        register(first_client, "revocation@example.com")
        captured_cookie = first_client.cookies.get("image_studio_session")
        assert captured_cookie
        assert first_client.post("/api/auth/logout").status_code == 204
        first_client.cookies.set("image_studio_session", captured_cookie)
        assert first_client.get("/api/auth/me").status_code == 401

        second_client = TestClient(app)
        with second_client:
            assert (
                second_client.post(
                    "/api/auth/login",
                    json={
                        "email": "revocation@example.com",
                        "password": "strong-pass-123",
                    },
                ).status_code
                == 200
            )
            assert second_client.get("/api/auth/me").status_code == 200

    restarted = create_app(settings=settings, provider=FakeProvider())
    with TestClient(restarted) as restarted_client:
        restarted_client.cookies.set("image_studio_session", captured_cookie)
        assert restarted_client.get("/api/auth/me").status_code == 401


def test_logout_with_invalid_cookie_does_not_create_revocation_record(
    client: TestClient,
) -> None:
    client.cookies.set("image_studio_session", "junk-cookie")
    assert client.post("/api/auth/logout").status_code == 204
    with client.app.state.database.connections.connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM revoked_sessions").fetchone()[
            0
        ]
    assert count == 0


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
    assert file_response.headers["cache-control"] == "no-store"
    assert file_response.headers["x-content-type-options"] == "nosniff"
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


def test_edit_can_chain_from_previous_derived_image(
    client: TestClient, fake_provider: FakeProvider
) -> None:
    register(client, "chain@example.com")
    original = client.post("/api/images/generate", json={"prompt": "A mountain"}).json()

    first_result = _one_pixel_png((200, 40, 80, 255))
    fake_provider.image_data = first_result
    first_edit = client.post(
        f"/api/images/{original['id']}/edit",
        json={"prompt": "Add a red moon"},
    )
    assert first_edit.status_code == 201
    first_record = first_edit.json()
    assert first_record["parent_id"] == original["id"]
    assert client.get(first_record["file_url"]).content == first_result

    second_result = _one_pixel_png((20, 160, 90, 255))
    fake_provider.image_data = second_result
    second_edit = client.post(
        f"/api/images/{first_record['id']}/edit",
        json={"prompt": "Make the sky green"},
    )
    assert second_edit.status_code == 201
    second_record = second_edit.json()
    assert second_record["parent_id"] == first_record["id"]
    assert client.get(second_record["file_url"]).content == second_result
    assert fake_provider.calls[-1] == ("edit", "Make the sky green", first_result)


def test_openai_adapter_chained_edit_sends_previous_png_as_multipart_source(
    tmp_path: Path,
) -> None:
    requests: list[httpx.Request] = []
    original_result = _one_pixel_png((18, 52, 86, 255))
    first_result = _one_pixel_png((200, 40, 80, 255))
    second_result = _one_pixel_png((20, 160, 90, 255))
    responses = [original_result, first_result, second_result]

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        index = len(requests) - 1
        return httpx.Response(
            200,
            json={"data": [{"b64_json": base64.b64encode(responses[index]).decode()}]},
            request=request,
        )

    settings = make_settings(
        database_path=tmp_path / "chained-edit.sqlite3",
        image_storage_path=tmp_path / "chained-edit-images",
        frontend_dist_path=tmp_path / "frontend-dist",
    )
    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key=None,
        model="test-model",
        transport=httpx.MockTransport(respond),
    )
    try:
        with TestClient(
            create_app(settings=settings, provider=provider)
        ) as test_client:
            register(test_client, "adapter-chain@example.com")
            original = test_client.post(
                "/api/images/generate", json={"prompt": "A mountain"}
            ).json()
            first = test_client.post(
                f"/api/images/{original['id']}/edit",
                json={"prompt": "Add a red moon"},
            ).json()
            second = test_client.post(
                f"/api/images/{first['id']}/edit",
                json={"prompt": "Make the sky green"},
            ).json()

            assert first["parent_id"] == original["id"]
            assert second["parent_id"] == first["id"]
            assert len(requests) == 3
            second_request = requests[2]
            body = second_request.content
            assert second_request.headers["content-type"].startswith(
                "multipart/form-data;"
            )
            assert b'filename="source.png"' in body
            assert b"Content-Type: image/png" in body
            assert b"model" in body and b"test-model" in body
            assert b"prompt" in body and b"Make the sky green" in body
            assert b"output_format" in body and b"png" in body
            assert first_result in body
    finally:
        provider.close()


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
    assert client.delete(f"/api/images/{image['id']}").status_code == 404


def test_delete_removes_file_and_hides_record_but_preserves_child_lineage(
    client: TestClient,
) -> None:
    register(client, "delete@example.com")
    original = client.post("/api/images/generate", json={"prompt": "A tree"}).json()
    child = client.post(
        f"/api/images/{original['id']}/edit", json={"prompt": "Add stars"}
    ).json()
    file_path = client.app.state.storage.resolve(
        client.app.state.database.get_image(
            client.get("/api/auth/me").json()["id"], original["id"]
        ).file_path
    )
    assert file_path.exists()

    assert client.delete(f"/api/images/{original['id']}").status_code == 204
    assert not file_path.exists()
    assert client.delete(f"/api/images/{original['id']}").status_code == 404
    assert client.get(f"/api/images/{original['id']}").status_code == 404
    assert client.get(original["file_url"]).status_code == 404
    records = client.get("/api/images").json()
    assert [record["id"] for record in records] == [child["id"]]
    assert records[0]["parent_id"] == original["id"]
    assert client.get(child["file_url"]).status_code == 200


def test_delete_storage_failure_keeps_record_visible(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    register(client, "delete-failure@example.com")
    image = client.post("/api/images/generate", json={"prompt": "A lake"}).json()

    def fail_delete(_relative_path: str) -> None:
        raise ImageStorageError("Image storage is unavailable.")

    monkeypatch.setattr(client.app.state.storage, "delete", fail_delete)
    response = client.delete(f"/api/images/{image['id']}")
    assert response.status_code == 500
    assert client.get(f"/api/images/{image['id']}").status_code == 200
    assert client.get(image["file_url"]).status_code == 200


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


def test_structured_edit_rejection_is_persisted_as_safe_failure(
    tmp_path: Path,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/images/edits"):
            return httpx.Response(
                400,
                json={
                    "error": {
                        "code": "invalid_image",
                        "message": "private upstream prompt and filename",
                    }
                },
                request=request,
            )
        return httpx.Response(
            200,
            json={"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode()}]},
            request=request,
        )

    settings = make_settings(
        database_path=tmp_path / "provider-rejection.sqlite3",
        image_storage_path=tmp_path / "provider-rejection-images",
        frontend_dist_path=tmp_path / "frontend-dist",
    )
    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key=None,
        model="test-model",
        transport=httpx.MockTransport(respond),
    )
    try:
        with TestClient(
            create_app(settings=settings, provider=provider)
        ) as test_client:
            register(test_client, "structured-failure@example.com")
            original = test_client.post(
                "/api/images/generate", json={"prompt": "A mountain"}
            ).json()
            response = test_client.post(
                f"/api/images/{original['id']}/edit",
                json={"prompt": "Make it blue"},
            )

            assert response.status_code == 502
            assert response.json()["detail"] == (
                "Image provider rejected the source image. Check its format and size."
            )
            records = test_client.get("/api/images").json()
            failed = next(record for record in records if record["status"] == "failed")
            assert failed["parent_id"] == original["id"]
            assert failed["file_url"] is None
            assert failed["error"] == response.json()["detail"]
            assert "private" not in failed["error"]
            assert len(list(test_client.app.state.storage.root.rglob("*.png"))) == 1
    finally:
        provider.close()


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


def test_image_requests_stop_before_provider_when_daily_budget_is_exhausted(
    client: TestClient, fake_provider: FakeProvider
) -> None:
    register(client, "budget@example.com")
    for _ in range(24):
        assert (
            client.post(
                "/api/images/generate", json={"prompt": "A small tree"}
            ).status_code
            == 201
        )
    blocked = client.post("/api/images/generate", json={"prompt": "One more"})
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    assert blocked.headers["cache-control"] == "no-store"
    assert len(fake_provider.calls) == 24
    assert len(client.get("/api/images").json()) == 24


def test_login_attempts_are_limited_without_account_existence_disclosure(
    client: TestClient,
) -> None:
    for _ in range(20):
        response = client.post(
            "/api/auth/login",
            json={"email": "unknown@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401
    blocked = client.post(
        "/api/auth/login",
        json={"email": "unknown@example.com", "password": "wrong-password"},
    )
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_unknown_account_still_runs_password_verification(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    app_module = importlib.import_module("image_studio.app")
    actual_verify = app_module.verify_password
    checked_hashes = []

    def record_verify(password: str, encoded: str) -> bool:
        checked_hashes.append(encoded)
        return actual_verify(password, encoded)

    monkeypatch.setattr(app_module, "verify_password", record_verify)
    response = client.post(
        "/api/auth/login",
        json={"email": "unknown@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert len(checked_hashes) == 1
    assert checked_hashes[0].startswith("scrypt$")


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


def test_adapter_rejects_oversized_streamed_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from image_studio.ai import openai_compatible

    monkeypatch.setattr(openai_compatible, "MAX_PROVIDER_RESPONSE_BYTES", 32)
    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key=None,
        model="test-model",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                stream=httpx.ByteStream(b"{" + b"a" * 33),
                request=request,
            )
        ),
    )
    try:
        with pytest.raises(ImageProviderError, match="response is too large"):
            provider.generate("A lantern")
    finally:
        provider.close()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            {"code": "invalid_image", "message": "private source details"},
            "source image",
        ),
        (
            {"code": "image_edit_not_supported", "message": "private details"},
            "does not support this image edit",
        ),
        (
            {"code": "unsupported_parameter", "param": "output_format"},
            "'output_format' image parameter",
        ),
    ],
)
def test_adapter_maps_structured_edit_rejections_safely(
    error: dict[str, str], expected: str
) -> None:
    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key=None,
        model="test-model",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(400, json={"error": error}, request=request)
        ),
    )
    try:
        with pytest.raises(ImageProviderError, match=expected) as raised:
            provider.edit("Make it blue", PNG_BYTES, "image/png")
        assert "private" not in str(raised.value)
    finally:
        provider.close()


def test_adapter_keeps_generic_message_for_unknown_rejection() -> None:
    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key=None,
        model="test-model",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                422,
                json={"error": {"code": "vendor_secret", "message": "private"}},
                request=request,
            )
        ),
    )
    try:
        with pytest.raises(
            ImageProviderError,
            match="rejected this prompt or source image",
        ) as raised:
            provider.edit("Make it blue", PNG_BYTES, "image/png")
        assert "private" not in str(raised.value)
    finally:
        provider.close()


def test_adapter_maps_typed_rejection_without_code_safely() -> None:
    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key=None,
        model="test-model",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                400,
                json={
                    "error": {
                        "type": "invalid_request_error",
                        "param": "image",
                        "message": "private source details",
                    }
                },
                request=request,
            )
        ),
    )
    try:
        with pytest.raises(
            ImageProviderError, match="'image' image parameter"
        ) as raised:
            provider.edit("Make it blue", PNG_BYTES, "image/png")
        assert "private" not in str(raised.value)
    finally:
        provider.close()


def test_adapter_includes_status_for_unstructured_rejection() -> None:
    provider = OpenAICompatibleProvider(
        base_url="http://images.internal/v1",
        api_key=None,
        model="test-model",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                422, text="upstream details", request=request
            )
        ),
    )
    try:
        with pytest.raises(ImageProviderError, match="HTTP 422") as raised:
            provider.edit("Make it blue", PNG_BYTES, "image/png")
        assert "upstream details" not in str(raised.value)
    finally:
        provider.close()
