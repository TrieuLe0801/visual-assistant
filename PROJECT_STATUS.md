# Project Status

Last updated: 2026-11-08

## Current milestone

MVP implemented and offline verified. Live OpenAI and self-hosted provider
checks remain pending because no real credentials or endpoint were supplied for
this verification.

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

## Implementation status

| Bước | Trạng thái | Bằng chứng |
|---|---|---|
| 1. Tài khoản, quyền sở hữu và lưu trữ bền vững | Hoàn thành | Auth, owner-isolation, file access và restart tests |
| 2. Generation, edit, variation và provider errors | Hoàn thành offline | Fake-provider, adapter, unsupported capability, invalid/oversized image và storage-failure tests |
| 3. Giao diện và production build | Hoàn thành offline | SPA/static tests; TypeScript + Vite build passed |
| 4. Live OpenAI/self-hosted smoke tests | Chưa chạy | Cần endpoint và credentials; không có model call trong lần kiểm chứng này |

## Now

1. Configure `SESSION_SECRET` before any non-development deployment.
2. When credentials and endpoint are available, run separate OpenAI and
   self-hosted generation/edit/variation smoke checks.
3. Define a backup procedure for SQLite and the local image volume before
   storing production data.

## Next

- Record live provider results and any provider-specific capability gaps.
- Consider asynchronous jobs or object storage only if real deployment needs
  require them.

## Dependencies and limits

The default provider/model are admin configuration; the UI does not expose
them. Live provider behavior remains unverified. SQLite and local files target a
single application host; backup and multi-host coordination are not included.
Provider calls run synchronously, so a request can remain open while an image
is generated.

## Verification

- Project Python: CPython 3.10.21 via uv; system `python3` is 3.9.6.
- `uv sync --locked`: passed; 37 packages checked.
- `uv lock --check`: passed; 41 packages resolved.
- `uv run pytest tests/test_image_studio.py`: 15 passed.
- `uv run pytest`: 17 passed (15 application tests and 2 development-hook tests).
- isort, Black, flake8 and Ruff standard checks: passed.
- `npm ci --offline`: passed; no vulnerabilities reported.
- `npm run build`: passed with Vite 8.3.6.
- `git diff --check`: passed.
- Live provider calls and browser-driven E2E: not run.
