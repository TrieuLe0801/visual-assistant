# Project Status

Last updated: 2026-11-10

## Current milestone

MVP implemented. Users can select 1–6 images per creation action and delete
images from their library. Offline tests and the frontend build pass. The
updated backend/frontend are running in the existing Compose stack; local and
public health checks returned HTTP 200. Live image generation still needs a
browser retry.

Security audit fixes are implemented and verified offline in this worktree:
explicit session secret, Secure cookie default, API no-store headers, persistent
safety rate limits, bounded provider responses and Pillow 13 in the Python 3.11
Trixie deployment image. Docker Scout found 27 residual runtime advisories,
none high or critical. The running Compose stack has **not** been updated with these
security changes. See [audit report](docs/security-audit-2026-11-10.md) and
[ADR 0010](docs/adr/0010-security-guards.md).

Active plan: [docs/implementation-plan.md](docs/implementation-plan.md).
Active charter: [docs/project-charter.md](docs/project-charter.md).
Current log: [docs/learning-log/2026-11-08-image-studio.md](docs/learning-log/2026-11-08-image-studio.md).

The image-studio scope replaces the travel-planner product. The previous
charter and implementation plan are preserved under
[`docs/archive/2026-10-14/`](docs/archive/2026-10-14/README.md). No travel
planner completion counts carry forward.

## Done

- Recorded image-studio requirements, provider/storage decisions, MVP limits
  and acceptance scenarios in the charter and [ADR 0005](docs/adr/0005-ai-image-studio.md).
- Implemented FastAPI email/password auth, signed sessions, SQLite records,
  owner-scoped image access and local-volume storage.
- Added provider interface and OpenAI/OpenAI-compatible adapters for image
  generation, editing and variations.
- Added prompt/status/metadata persistence, source relationships, image
  validation, 20 MiB output limit and safe provider/storage failures.
- Built React/TypeScript screens for auth, library, prompt creation, image
  details, edit, variation and download.
- Added offline tests with fake provider and HTTP transport. Full suite passes.
- Added frontend lockfile and recorded the active environment baseline.
- Split backend into AI services, SQLite settings/connection/repository modules,
  and reusable security/image/time utilities without changing API routes.
- Added server-selected LangChain Core model routing and metadata-only LangSmith
  operation traces; see [ADR 0006](docs/adr/0006-langchain-model-routing-langsmith-tracing.md).
- Added server-side Vietnamese prompt interpretation for generation, editing and
  variations; the library retains the user's original text. See
  [ADR 0008](docs/adr/0008-vietnamese-prompt-interpretation.md).
- Added a 1–6 image selector that makes separate requests, plus owner-scoped
  deletion of image files and library entries. Derived image records keep their
  source relationship; see [ADR 0009](docs/adr/0009-image-batch-and-deletion.md).
- Built an arm64 Docker image and healthy single-host Compose container with a
  persistent SQLite/image volume and file-backed session secret. A stopped-app
  backup restored successfully into a separate verification volume; see
  [deployment guide](docs/deployment-compose-cloudflare.md) and [ADR 0007](docs/adr/0007-single-host-compose-cloudflare.md).
- Split Compose into a one-shot SQLite schema initializer, FastAPI backend,
  Nginx frontend and optional Cloudflare Quick Tunnel service. The tunnel is
  running; its temporary public `/api/health` returned HTTP 200.
- Audited source and dependencies; patched confirmed session, abuse, response
  buffering, cache and account-timing risks. Python 3.10 still resolves Pillow
  12.3.0 with known advisories; use Python 3.11 for deployment.

## Implementation status

| Bước | Trạng thái | Bằng chứng |
|---|---|---|
| 1. Tài khoản, quyền sở hữu và lưu trữ bền vững | Hoàn thành | Auth, owner-isolation, file access và restart tests |
| 2. Generation, edit, variation và provider errors | Hoàn thành offline | Fake-provider, adapter, unsupported capability, invalid/oversized image và storage-failure tests |
| 2a. LangChain model routing và LangSmith tracing | Hoàn thành offline | 6 model-routing/trace tests; chưa xác nhận LangSmith remote |
| 2b. Hiểu prompt tiếng Việt | Offline verified; live model còn chờ | 2 HTTP mock/API tests qua; latest source image đã deploy nhưng chưa kiểm tra live prompt |
| 3. Giao diện và production build | Hoàn thành offline | SPA/static tests; TypeScript + Vite build passed |
| 4. Live OpenAI/self-hosted smoke tests | Đang chờ retry generation | Lần gần nhất 502 do container chưa nhận key; backend đã recreate; GET `/models` 200, model cấu hình có trong danh sách |
| 5. Docker Compose local deployment | Hoàn thành | backend/frontend images, database init exit 0, both long-running services healthy, HTTP proxy, backup/restore |
| 6. Cloudflare public tunnel | Quick Tunnel đang chạy; URL tạm thời | Cloudflare returned HTTP 200 for public `/api/health`; no named domain or Access policy |
| 7. Chọn 1–6 ảnh và xóa ảnh | Đã deploy; live generation còn chờ | Offline API tests, frontend build, Compose health và public health qua |
| 8. Security audit và vá lỗi | Hoàn thành offline; chưa deploy | 40 tests trên Python 3.10 và 3.11, style checks, dependency audit, frontend build, isolated Docker build |

## Now

1. Retry image generation in the browser, including a multi-image action.
   Verify prompt interpretation and output separately from health checks.
2. Review and roll out the security-patched images with a data backup; the
   current public stack still runs the prior image.
3. If a stable public hostname is needed, create a named Cloudflare Tunnel,
   configure its DNS routes and restrict access with Cloudflare Access.
4. Verify `PROMPT_MODEL` against the configured API, then run separate OpenAI
   and self-hosted operation checks.
5. Schedule off-host copies of the documented stopped-app backup before
   storing production data.

## Next

- Record live provider results and any provider-specific capability gaps.
- Consider asynchronous jobs or object storage only if real deployment needs
  require them.

## Dependencies and limits

The default provider/model are admin configuration; the UI does not expose
them. `IMAGE_MODEL_CATALOG` and `IMAGE_ACTIVE_MODEL` select a server-side model
at startup. LangSmith tracing is opt-in and excludes prompt/image content.
Live provider behavior and remote trace delivery remain unverified. SQLite and local files target a
single application host; a manual backup/restore path exists, but scheduled
off-host backup and multi-host coordination are not included.
Each prompt is also sent to the configured language model for interpretation;
this adds a model request, latency and cost before the image-provider request.
Provider calls run synchronously, so a request can remain open while an image
is generated.

## Verification

- Project Python: CPython 3.10.21 via uv; system `python3` is 3.9.6.
- `uv sync --locked`: passed; 58 packages checked.
- `uv lock --check`: passed; 66 packages resolved.
- `uv run pytest tests/test_image_studio.py`: 15 passed.
- `uv run pytest tests/test_model_routing.py`: 6 passed.
- `uv run pytest`: 30 passed (28 application/deployment tests and 2 development-hook tests).
- `uv run pytest tests/test_database.py tests/test_image_studio.py`: 17 passed.
- isort, Black, flake8 and Ruff standard checks: passed.
- `npm ci --offline`: passed; no vulnerabilities reported.
- `npm run build`: passed with Vite 8.3.6.
- `git diff --check`: passed.
- Vietnamese prompt interpreter change (2026-11-09): 2 focused HTTP mock/API
  tests passed; full pytest suite 29 passed. isort, Black, flake8, Ruff,
  frontend TypeScript/Vite build, Compose config and diff check passed. Live
  prompt and image calls remain unverified.
- `docker compose config --quiet`, `docker compose --profile publish config --quiet`,
  `docker compose build app frontend` and `docker compose up -d --wait`: passed.
- Database initializer exited 0. Backend and frontend healthy. Local
  `/api/health`, frontend root and SPA route: HTTP 200; unauthenticated
  `/api/images`: HTTP 401. Backend has no host port.
- Compose secret and Secure cookie configuration confirmed inside backend.
  Internal Compose-network request to `frontend:80/api/health`: HTTP 200.
- Stopped-app volume backup restored into a separate volume; SQLite integrity
  check: `ok`; image directory present.
- Cloudflare Quick Tunnel started in Compose with image
  `cloudflare/cloudflared:latest`; connector registered over QUIC. Public
  `/api/health` returned HTTP 200. URL is temporary and has no Access policy.
- User's image-generation attempt returned HTTP 502. Cloudflare health stayed
  HTTP 200. At failure time, `.env` had an OpenAI key but the backend container
  had no `OPENAI_API_KEY`; the failed operation recorded a credentials error.
- Recreated only the backend with
  `docker compose up -d --no-deps --force-recreate app`. It is healthy and now
  has the key. Read-only OpenAI `GET /models`: HTTP 200; configured image model
  listed. No image-generation request was retried.
- Live image generation, prompt interpretation, LangSmith remote delivery and
  browser-driven E2E remain unverified.
- Delete/count deployment (2026-11-09): focused `uv run pytest
  tests/test_database.py tests/test_image_studio.py -q` passed (20 tests);
  full `uv run pytest` passed (32 tests); isort, Black, flake8, Ruff and
  `git diff --check` passed;
  frontend `npm run build` passed. New backend and frontend images built and
  healthy in the existing `visual-assistant` Compose project. Stopped-app
  backup passed `gzip -t`; SQLite `PRAGMA integrity_check` returned `ok`, and
  the new `deleted_at` column exists. Local `/api/health` and frontend returned
  HTTP 200; unauthenticated DELETE returned 401. Public Quick Tunnel
  `/api/health` returned HTTP 200. Live image creation and browser UI behavior
  were not tested.
