# Learning Log — AI image studio MVP

Date: 2026-11-08
Status: Current

## Objective

Replace the travel planner product with a personal webapp for image generation,
prompt-based editing, variations and persistent image history.

## Changes

- Replaced active project charter, implementation plan, UI plan, status, roadmap,
  environment template and Codex product instructions. Preserved previous
  sightseeing requirements and plan under `docs/archive/2026-10-14/`.
- Added ADR 0005 for FastAPI, React/TypeScript, email/password auth, SQLite,
  local image storage, provider adapters and owner-scoped access.
- Added FastAPI auth, HMAC session cookies, scrypt password hashes, SQLite
  records, local image files and owner-scoped image/detail/download endpoints.
- Added provider contract and OpenAI-compatible image generation/edit adapter.
  Admin config selects provider, model, endpoint and credentials through
  environment variables. The user interface does not expose provider settings.
- Added generation, edit and variation history, with prompt and parent-image
  relationships. Variation uses the supported image-edit contract. It does not
  call the deprecated legacy variations endpoint.
- Validated returned PNG/JPEG/WebP files with Pillow. Rejected malformed images,
  files above 20 MiB and images above 40 megapixels before storage.
- Added Vietnamese React UI for auth, library, image detail/download, create,
  edit and variation. Added Vite development proxy and production build serving.
- Added deterministic fake-provider and HTTP-transport tests. Added
  `python-dotenv`, runtime dependencies, uv lock and npm lockfile.

OpenAI's [image guide](https://developers.openai.com/api/docs/guides/image-generation)
documents image generation and edits. The
[Images API reference](https://developers.openai.com/api/reference/resources/images)
marks the legacy image-variation endpoint deprecated. This supports routing
variation through the edit adapter, with a clear unsupported error when edits
are unavailable.

## Environment recorded

- CPython 3.10.21 through `uv run`; system `python3` is 3.9.6.
- `uv` 0.12.19.
- Node.js v24.13.0 and npm 11.6.2.
- Vite 8.3.6.
- See [image-studio environment baseline](../experiments/image-studio-environment.md).

## Verification

- `uv lock --check --cache-dir /private/tmp/visual-assistant-uv-cache`: passed.
- `uv sync --locked --cache-dir /private/tmp/visual-assistant-uv-cache`: passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest tests/test_image_studio.py`: 15 passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest`: 17 passed, including 2 development-hook tests.
- Standard isort, Black, flake8 and Ruff commands with the temporary uv cache: passed.
- `git diff --check`: passed.
- `npm ci --offline --cache /private/tmp/image-studio-npm-cache`: passed; no vulnerabilities reported.
- `npm run build`: passed; TypeScript check and Vite production build completed.

The test suite covers registration/login/logout, password policy, generation,
edit/variation source relationships, user isolation, provider failures,
unsupported operations, malformed/oversized images, storage failure,
application restart, API payloads and SPA static serving.

## Limits

Live OpenAI and self-hosted provider checks were not run. No API credential or
self-hosted endpoint was supplied for this verification. No generated image
model calls occurred. Browser-driven end-to-end interaction was also not run;
the frontend TypeScript/Vite build and backend SPA tests passed.

SQLite plus a local volume serves a single host. Backup/restore and multi-host
coordination are not implemented. Provider calls are synchronous.

## Codex workflow refresh — 2026-11-08

- Set the project coordinator, manager, and planner to `gpt-6-sol`; set coding,
  testing, and deploying agents to `gpt-5.6-luna`.
- Added the deploying role and `project-deployment` skill, based on current
  secret, single-host storage, backup, and live-provider constraints.
- Retained the project workflow-transfer and verification skills. Used the
  global `repo-delivery` and `skill-creator` guidance as input; did not copy
  personal skill directories or plugin caches into the repository.
- Updated `AGENTS.md` and this workflow guide with role, model, and skill
  assignments.

### Verification

- `codex debug models | jq -r '.models[].slug' | sort | rg '^(gpt-6-sol|gpt-5\.6-luna)$'`:
  both model IDs appear in the local Codex model catalog.
- `uv run --with tomli --with PyYAML python` with inline assertions: project
  config and five agent TOMLs parsed; model assignments matched; deployment
  skill frontmatter and UI metadata parsed successfully.
- `git diff --check -- .codex/config.toml .codex/agents AGENTS.md docs/codex-workflow.md .agents/skills/project-deployment`:
  passed.
- Application tests were not run for this configuration change.
- `codex debug` does not support `--strict-config`; TOML parsing above checks
  project and agent syntax directly.
