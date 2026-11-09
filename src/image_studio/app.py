"""FastAPI application for private AI image creation and editing."""

import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .ai import (
    ImageOperationError,
    ImageProvider,
    ImageService,
    PromptEnhancer,
    build_prompt_enhancer,
    build_provider,
)
from .config import Settings
from .database import Database, ImageRecord, User
from .storage import LocalImageStorage
from .utils.image import IMAGE_EXTENSIONS, ImageStorageError
from .utils.security import SessionCodec, hash_password, verify_password

SESSION_COOKIE_NAME = "image_studio_session"
MAX_PROMPT_LENGTH = 4000
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class CredentialsInput(BaseModel):
    email: str
    password: str


class PromptInput(BaseModel):
    prompt: str


class VariationInput(BaseModel):
    prompt: str | None = None


class UserOutput(BaseModel):
    id: str
    email: str
    created_at: str


class ImageOutput(BaseModel):
    id: str
    prompt: str
    operation: str
    status: str
    parent_id: str | None
    created_at: str
    provider: str
    model: str
    mime_type: str | None
    size_bytes: int | None
    error: str | None
    file_url: str | None


def create_app(
    *,
    settings: Settings | None = None,
    provider: ImageProvider | None = None,
    prompt_enhancer: PromptEnhancer | None = None,
    database: Database | None = None,
    storage: LocalImageStorage | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.validate()
    injected_provider = provider is not None
    session_codec = SessionCodec(settings.session_secret, settings.session_ttl_seconds)
    database = database or Database(settings.database)
    storage = storage or LocalImageStorage(settings.image_storage_path)
    provider = provider or build_provider(settings)
    if prompt_enhancer is None and not injected_provider:
        prompt_enhancer = build_prompt_enhancer(settings)
    image_service = ImageService(database, storage, provider, prompt_enhancer)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        database.initialize()
        storage.initialize()
        try:
            yield
        finally:
            close = getattr(provider, "close", None)
            if callable(close):
                close()
            close_prompt_model = getattr(prompt_enhancer, "close", None)
            if callable(close_prompt_model):
                close_prompt_model()

    app = FastAPI(
        title="Image Studio API",
        version="0.1.0",
        description="Private AI image generation, editing, and variation library.",
        lifespan=lifespan,
    )

    def require_user(request: Request) -> User:
        token = request.cookies.get(SESSION_COOKIE_NAME)
        user_id = session_codec.read(token) if token else None
        user = database.get_user_by_id(user_id) if user_id else None
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please sign in to continue.",
            )
        return user

    @app.get("/api/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/auth/register", response_model=UserOutput, status_code=201)
    def register(payload: CredentialsInput, response: Response) -> UserOutput:
        email = _normalize_email(payload.email)
        _validate_email(email)
        _validate_password(payload.password)
        if database.get_user_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
        try:
            user = database.create_user(email, hash_password(payload.password))
        except Exception as exc:
            # SQLite uniqueness remains authoritative if two registrations race.
            if database.get_user_by_email(email) is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists.",
                ) from exc
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account could not be created.",
            ) from exc
        _set_session_cookie(response, session_codec, settings, user.id)
        return _user_output(user)

    @app.post("/api/auth/login", response_model=UserOutput)
    def login(payload: CredentialsInput, response: Response) -> UserOutput:
        email = _normalize_email(payload.email)
        user = database.get_user_by_email(email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
            )
        _set_session_cookie(response, session_codec, settings, user.id)
        return _user_output(user)

    @app.post("/api/auth/logout", status_code=204)
    def logout(response: Response) -> Response:
        response.delete_cookie(
            SESSION_COOKIE_NAME,
            path="/",
            httponly=True,
            secure=settings.session_cookie_secure,
            samesite="strict",
        )
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @app.get("/api/auth/me", response_model=UserOutput)
    def get_current_user(
        user: Annotated[User, Depends(require_user)],
    ) -> UserOutput:
        return _user_output(user)

    @app.get("/api/images", response_model=list[ImageOutput])
    def list_images(
        user: Annotated[User, Depends(require_user)],
    ) -> list[ImageOutput]:
        return [_image_output(record) for record in database.list_images(user.id)]

    @app.get("/api/images/{image_id}", response_model=ImageOutput)
    def get_image(
        image_id: str, user: Annotated[User, Depends(require_user)]
    ) -> ImageOutput:
        record = _owned_image(database, user.id, image_id)
        return _image_output(record)

    @app.get("/api/images/{image_id}/file")
    def get_image_file(
        image_id: str, user: Annotated[User, Depends(require_user)]
    ) -> FileResponse:
        record = _owned_image(database, user.id, image_id)
        if record.status != "succeeded" or not record.file_path or not record.mime_type:
            raise HTTPException(status_code=404, detail="Image file was not found.")
        try:
            image_path = storage.resolve(record.file_path)
        except ImageStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image file was not found.",
            ) from exc
        return FileResponse(
            image_path,
            media_type=record.mime_type,
            filename=f"image-{record.id}.{_mime_extension(record.mime_type)}",
            content_disposition_type="inline",
        )

    @app.post("/api/images/generate", response_model=ImageOutput, status_code=201)
    def generate_image(
        payload: PromptInput, user: Annotated[User, Depends(require_user)]
    ) -> ImageOutput:
        prompt = _validate_prompt(payload.prompt)
        return _run_operation(
            service=image_service,
            owner_id=user.id,
            prompt=prompt,
            operation="generate",
            parent_id=None,
        )

    @app.post(
        "/api/images/{image_id}/edit", response_model=ImageOutput, status_code=201
    )
    def edit_image(
        image_id: str,
        payload: PromptInput,
        user: Annotated[User, Depends(require_user)],
    ) -> ImageOutput:
        prompt = _validate_prompt(payload.prompt)
        parent = _owned_image(database, user.id, image_id)
        source, mime_type = _read_source(storage, parent)
        return _run_operation(
            service=image_service,
            owner_id=user.id,
            prompt=prompt,
            operation="edit",
            parent_id=parent.id,
            source=(source, mime_type),
        )

    @app.post(
        "/api/images/{image_id}/variations",
        response_model=ImageOutput,
        status_code=201,
    )
    def create_variation(
        image_id: str,
        payload: VariationInput,
        user: Annotated[User, Depends(require_user)],
    ) -> ImageOutput:
        variation_prompt = (payload.prompt or "").strip()
        prompt = _validate_prompt(
            variation_prompt or "Tạo một biến thể khác biệt từ ảnh gốc."
        )
        parent = _owned_image(database, user.id, image_id)
        source, mime_type = _read_source(storage, parent)
        return _run_operation(
            service=image_service,
            owner_id=user.id,
            prompt=prompt,
            operation="variation",
            parent_id=parent.id,
            source=(source, mime_type),
        )

    app.state.database = database
    app.state.storage = storage
    app.state.provider = provider
    app.state.image_service = image_service
    app.state.settings = settings
    app.state.session_codec = session_codec
    _mount_frontend(app, settings.frontend_dist_path)
    return app


def _run_operation(
    *,
    service: ImageService,
    owner_id: str,
    prompt: str,
    operation: str,
    parent_id: str | None,
    source: tuple[bytes, str] | None = None,
) -> ImageOutput:
    try:
        record = service.run(
            owner_id=owner_id,
            prompt=prompt,
            operation=operation,
            parent_id=parent_id,
            source=source,
        )
    except ImageOperationError as exc:
        code = {
            "storage": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "unsupported": status.HTTP_501_NOT_IMPLEMENTED,
            "provider": status.HTTP_502_BAD_GATEWAY,
        }[exc.reason]
        raise HTTPException(status_code=code, detail=exc.detail) from exc
    return _image_output(record)


def _mount_frontend(app: FastAPI, distribution: Path) -> None:
    root = distribution.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> Response:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route was not found.")
        if not root.is_dir():
            raise HTTPException(status_code=404, detail="Frontend build was not found.")
        requested = (root / path).resolve()
        if root not in requested.parents and requested != root:
            raise HTTPException(status_code=404, detail="File was not found.")
        if requested.is_file():
            return FileResponse(requested)
        if not Path(path).suffix:
            index_file = root / "index.html"
            if index_file.is_file():
                return FileResponse(index_file, media_type="text/html")
        raise HTTPException(status_code=404, detail="File was not found.")


def _owned_image(database: Database, owner_id: str, image_id: str) -> ImageRecord:
    record = database.get_image(owner_id, image_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Image was not found.")
    return record


def _read_source(storage: LocalImageStorage, record: ImageRecord) -> tuple[bytes, str]:
    if record.status != "succeeded" or not record.file_path or not record.mime_type:
        raise HTTPException(status_code=409, detail="Source image is not available.")
    try:
        return storage.resolve(record.file_path).read_bytes(), record.mime_type
    except (ImageStorageError, OSError) as exc:
        raise HTTPException(
            status_code=404, detail="Source image file was not found."
        ) from exc


def _validate_prompt(prompt: str) -> str:
    cleaned = prompt.strip()
    if not cleaned:
        raise HTTPException(status_code=422, detail="Prompt must not be empty.")
    if len(cleaned) > MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Prompt must be {MAX_PROMPT_LENGTH} characters or fewer.",
        )
    return cleaned


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_email(email: str) -> None:
    if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")


def _validate_password(password: str) -> None:
    if len(password) < 10 or len(password) > 128:
        raise HTTPException(
            status_code=422,
            detail="Password must contain between 10 and 128 characters.",
        )


def _set_session_cookie(
    response: Response,
    codec: SessionCodec,
    settings: Settings,
    user_id: str,
) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=codec.issue(user_id),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="strict",
        path="/",
    )


def _user_output(user: User) -> UserOutput:
    return UserOutput(id=user.id, email=user.email, created_at=user.created_at)


def _image_output(record: ImageRecord | None) -> ImageOutput:
    if record is None:
        raise HTTPException(status_code=500, detail="Image operation record was lost.")
    return ImageOutput(
        id=record.id,
        prompt=record.prompt,
        operation=record.operation,
        status=record.status,
        parent_id=record.parent_id,
        created_at=record.created_at,
        provider=record.provider,
        model=record.model,
        mime_type=record.mime_type,
        size_bytes=record.size_bytes,
        error=record.error,
        file_url=(
            f"/api/images/{record.id}/file" if record.status == "succeeded" else None
        ),
    )


def _mime_extension(mime_type: str) -> str:
    return IMAGE_EXTENSIONS.get(mime_type, "img")


app = create_app()
