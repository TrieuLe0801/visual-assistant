"""Offline checks for prompt interpretation and image-operation outcomes."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from PIL import Image

from image_studio.ai import (
    GeneratedImage,
    OpenAICompatiblePromptEnhancer,
    PromptEnhancer,
)
from image_studio.app import create_app
from image_studio.config import make_settings


def _png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (1, 1), "blue").save(buffer, format="PNG")
    return buffer.getvalue()


class _RecordingProvider:
    name = "fake"
    model = "fake-image"

    def __init__(self) -> None:
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


def _client(
    tmp_path: Path, provider: _RecordingProvider, enhancer: PromptEnhancer
) -> TestClient:
    settings = make_settings(
        database_path=tmp_path / "images.sqlite3",
        image_storage_path=tmp_path / "images",
        frontend_dist_path=tmp_path / "frontend",
    )
    return TestClient(
        create_app(settings=settings, provider=provider, prompt_enhancer=enhancer)
    )


def _register(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "prompt@example.com", "password": "strong-pass-123"},
    )
    assert response.status_code == 201


def test_vietnamese_prompt_is_interpreted_and_original_is_saved(tmp_path: Path) -> None:
    requests: list[dict[str, object]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "English image instruction"}}]},
        )

    enhancer = OpenAICompatiblePromptEnhancer(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model="test-chat",
        transport=httpx.MockTransport(respond),
    )
    provider = _RecordingProvider()
    try:
        with _client(tmp_path, provider, enhancer) as client:
            _register(client)
            generated = client.post(
                "/api/images/generate", json={"prompt": "Một ngôi nhà màu xanh"}
            )
            assert generated.status_code == 201
            source_id = generated.json()["id"]
            edited = client.post(
                f"/api/images/{source_id}/edit",
                json={"prompt": "Thêm chữ Xin chào"},
            )
            variation = client.post(
                f"/api/images/{source_id}/variations",
                json={"prompt": "Trời mưa"},
            )

            assert edited.status_code == variation.status_code == 201
            assert [item["prompt"] for item in client.get("/api/images").json()] == [
                "Trời mưa",
                "Thêm chữ Xin chào",
                "Một ngôi nhà màu xanh",
            ]
            assert provider.calls == [
                ("generate", "English image instruction"),
                ("edit", "English image instruction"),
                ("variation", "English image instruction"),
            ]
            assert [item["messages"][1]["content"] for item in requests] == [
                "Một ngôi nhà màu xanh",
                "Thêm chữ Xin chào",
                "Trời mưa",
            ]
            assert [item["model"] for item in requests] == ["test-chat"] * 3
    finally:
        enhancer.close()


def test_prompt_model_failure_stops_image_provider_and_records_failure(
    tmp_path: Path,
) -> None:
    enhancer = OpenAICompatiblePromptEnhancer(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model="test-chat",
        transport=httpx.MockTransport(lambda request: httpx.Response(503)),
    )
    provider = _RecordingProvider()
    try:
        with _client(tmp_path, provider, enhancer) as client:
            _register(client)
            response = client.post(
                "/api/images/generate", json={"prompt": "Một con mèo"}
            )

            assert response.status_code == 502
            assert response.json()["detail"] == (
                "Prompt language model could not process this description."
            )
            assert provider.calls == []
            record = client.get("/api/images").json()[0]
            assert record["prompt"] == "Một con mèo"
            assert record["status"] == "failed"
            assert record["file_url"] is None
    finally:
        enhancer.close()
