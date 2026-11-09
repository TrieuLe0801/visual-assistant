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

## Backend module refactor — 2026-11-08

- Moved provider contracts, OpenAI-compatible adapter, provider construction
  and image-operation coordination into `src/image_studio/ai/`. FastAPI routes
  now translate service failures into HTTP responses.
- Split SQLite environment settings, connection/transaction handling, schema,
  record models and owner-scoped repository into `src/image_studio/database/`.
- Moved reusable password/session, image validation and UTC timestamp helpers
  into `src/image_studio/utils/`. Kept local file persistence in `storage.py`.
- Added tests for database path configuration, transaction rollback and SQLite
  foreign-key enforcement. Updated imports in existing API tests and documented
  backend modules in `README.md`.
- The refactor does not change a confirmed architecture decision, so ADR 0005
  remains in force. No roadmap item was closed by this maintenance change.

### Verification

- `uv run pytest tests/test_database.py tests/test_image_studio.py`: 17 passed.
- `uv run pytest`: 23 passed, including 2 development-hook tests and 4
  model-routing tests added concurrently.
- `uv run isort --check-only . .codex/hooks/format_python.py`: passed.
- `uv run black --check . .codex/hooks/format_python.py`: passed.
- `uv run flake8 . .codex/hooks/format_python.py`: passed.
- `uv run ruff check . .codex/hooks/format_python.py`: passed after fixing an
  import rule in the concurrent model-router addition.
- `uv lock --check`: passed; 66 packages resolved with concurrent dependency
  additions present in the workspace.
- `git diff --check`: passed.
- `npm run build` in `frontend/`: passed (TypeScript and Vite build).
- Live provider calls, deployed-environment checks and browser-driven E2E:
  not run. This request changed local code structure only.

## LangChain model routing and LangSmith tracing — 2026-11-08

- Added LangChain Core runnable alternatives over the existing typed image
  provider contract. `IMAGE_MODEL_CATALOG` defines server-side aliases and
  `IMAGE_ACTIVE_MODEL` selects one at startup. Legacy single-model variables
  still work when the catalog is absent.
- Added LangSmith operation tracing, opt-in through environment variables.
  Traces contain operation, source presence, image ID, status, provider and
  model. Automatic runnable tracing is disabled around prompts and image bytes.
- Added offline tests for selection across generate/edit/variation, catalog
  parsing, invalid aliases, factory selection, trace redaction and credential
  omission from configuration representations. Added
  ADR 0006 and documented configuration in `.env.example` and `README.md`.
- No hosting target was specified. No external deployment was performed.
  SQLite/image-volume backup and restore remain a prerequisite for production
  data, and `SESSION_SECRET` must come from the deployment secret store.

### Verification

- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest tests/test_model_routing.py -q`: 6 passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest`: 25 passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run isort --check-only . .codex/hooks/format_python.py`: passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run black --check . .codex/hooks/format_python.py`: passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run flake8 . .codex/hooks/format_python.py`: passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run ruff check . .codex/hooks/format_python.py`: passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv lock --check`: passed; 66 packages resolved.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv sync --locked`: passed; 58 packages checked.
- `npm run build` in `frontend/`: passed with TypeScript and Vite 8.3.6.
- `git diff --check`: passed.
- Live OpenAI, self-hosted and LangSmith remote checks: not run. Credentials
  and a live self-hosted endpoint were not provided.

## Docker Compose and ngrok deployment — 2026-11-08

- Added a multi-stage Node/Python Dockerfile, `.dockerignore`, single-host
  `compose.yaml`, persistent named volume, app health check and localhost-only
  port binding. Compose injects the session secret from a file-backed secret.
- Added ignored local secret initializer and ngrok publish script. The ngrok
  endpoint uses Basic Auth before the app login. Added backup/restore and
  rollback instructions, plus ADR 0007.
- Generated a fresh ignored session secret and Basic Auth credential. No secret
  value was printed or committed. No provider or LangSmith key was present.
- Built and started the app container on Docker Desktop arm64. Stopped the app
  for a consistent volume backup, restored to a separate test volume, checked
  SQLite integrity and image directory, then removed that test volume. The
  initial verification archive is in ignored `backups/`.
- The host ngrok config has an authtoken, but its default dev domain is already
  online elsewhere. The attempted publish returned `ERR_NGROK_334`. The user
  will provide new ngrok variables. No public URL is claimed yet.

### Verification

- `docker compose config --quiet`: passed.
- `docker compose build app`: passed; `image-studio:local` is linux/arm64.
- `docker compose up -d --build --wait`: passed; app container healthy.
- `curl -fsS http://127.0.0.1:8000/api/health`: `{"status":"ok"}`.
- `curl -fsS http://127.0.0.1:8000/`: returned built React HTML.
- `docker compose exec -T app python -c ...`: session secret file loaded,
  Secure cookies enabled, image storage path `/data/images`.
- Stopped-app `docker run ... tar -czf` backup and separate-volume `tar -xzf`
  restore: passed. `PRAGMA integrity_check`: `ok`; image directory present.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest tests/test_deployment_config.py -q`: 2 passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest`: 27 passed.
- Standard isort, Black, flake8 and Ruff checks: passed.
- `npm run build`, `sh -n scripts/ngrok-publish.sh` and `git diff --check`: passed.
- Live provider, LangSmith remote delivery, public HTTPS and browser E2E:
  not run or not established. No provider credentials or new ngrok endpoint
  variables were supplied for those checks.

### ngrok `.env` configuration follow-up

- Updated host ngrok launcher to parse `NGROK_AUTHTOKEN` and optional
  `NGROK_URL` from ignored `.env` using `python-dotenv`. It does not shell-source
  `.env` or pass the token to the app container. Existing secret files and the
  ngrok CLI account config remain fallbacks.
- Added offline tests for `.env` precedence, URL validation and file fallback.
  The new ngrok variables were not present when this change was checked, so no
  new public tunnel was started.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest tests/test_ngrok_publish.py -q`: 3 passed.
- Full suite after this follow-up: 30 passed.

### Compose frontend, ngrok and database services

- Added a dedicated Nginx frontend image and Compose service. Nginx serves the
  React bundle, routes `/api/` to FastAPI and preserves SPA navigation. Only
  the frontend binds `127.0.0.1:8000`; backend is private to Compose.
- Added a one-shot `database` service using the backend image to initialize the
  SQLite schema on the existing persistent volume before the backend starts.
  SQLite remains embedded; no database server or multi-writer storage was added.
- Added `ngrok` under Compose profile `publish`, forwarding to `frontend:80`.
  The ngrok token/optional URL come from ignored `.env` only for this service;
  Basic Auth comes from a Compose secret. The prior host script remains an
  optional manual fallback.
- Updated ADR 0007, README, environment template and deployment guide. The
  ngrok token and URL remained unset, so the new public service was not started.

#### Verification

- `docker compose config --quiet` and
  `docker compose --profile publish config --quiet`: passed.
- `docker compose build app frontend`: passed; both images built for arm64.
- `docker compose up -d --wait`: passed. `database` exited 0; `app` and
  `frontend` healthy.
- Local HTTP: `/api/health` 200, `/` 200 HTML, `/images/example` 200 HTML,
  unauthenticated `/api/images` 401.
- SQLite `PRAGMA integrity_check`: `ok`; image directory persisted after
  Compose recreation.
- Temporary container on Compose network requested `frontend:80/api/health`:
  HTTP 200.
- Ngrok image has `/bin/sh` and `/bin/ngrok`; Basic Auth secret mounted;
  publish-profile shell command passed `sh -n`. No public tunnel check yet.
