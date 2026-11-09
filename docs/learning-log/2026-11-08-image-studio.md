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

### Frontend host port selection — 2026-11-09

- Docker showed the current frontend on host port 8000 and another project on
  port 8503. Host port 8088 had no listener.
- Changed the Compose frontend binding to `127.0.0.1:${FRONTEND_PORT:-8088}:80`.
  Added `FRONTEND_PORT` to `.env.example`; it can override the default if needed.
- Updated the local URL in the README, deployment guide and ADR 0007.
- Recreated only the frontend with `docker compose up -d --no-deps
  --force-recreate frontend`; its health check passed. The backend was not
  recreated.
- `curl -fsS http://127.0.0.1:8088/api/health`: `{"status":"ok"}`.

## Vietnamese prompt interpretation — 2026-11-09

- Added `ai/prompt_enhancer.py` to send Vietnamese or other-language input to a
  server-configured OpenAI-compatible chat model, then prepare an English image
  instruction for generation, edit and variation operations.
- The database and UI continue to use the original user prompt. Instructions
  preserve exact words requested for rendering. Prompt text remains excluded
  from LangSmith traces.
- Added `PROMPT_MODEL`, `PROMPT_API_BASE_URL`, `PROMPT_API_KEY` and
  `PROMPT_TIMEOUT_SECONDS` configuration to local settings and Compose. The
  prompt key falls back to `OPENAI_API_KEY` only when endpoints match;
  self-hosted endpoints use their own optional key.
- Updated the create UI, UI and implementation plans, README, product charter,
  deployment guide and ADR 0008.
- `.env` contains no OpenAI API key, so live prompt interpretation and image
  generation remain unavailable until a key or reachable compatible endpoint
  is configured.

### Verification

- No automated tests were added or run for this change.
- isort, Black, flake8 and Ruff: passed.
- `npm run build`: passed; TypeScript and Vite production build completed.
- `docker compose config --quiet` and `git diff --check`: passed.
- Live Vietnamese prompt and image-provider checks: not run; no credentials or
  endpoint were configured.
- No deployment or Compose restart was performed.

## Replace ngrok with Cloudflare Quick Tunnel — 2026-11-09

- Replaced the Compose `ngrok` publish service with `cloudflared` under the same
  optional `publish` profile. It routes to `frontend:80`; Quick Tunnel needs no
  token or domain. Removed the obsolete host ngrok launcher and its tests.
- Renamed the deployment guide and amended ADR 0007. Updated README, project
  status, roadmap and secret initialization. The old ignored `.env` ngrok keys
  and `.secrets/ngrok-basic-auth` file were left untouched; Compose no longer
  reads them.
- Docker showed Visual Assistant frontend on `127.0.0.1:8088`; the other project
  remains on `127.0.0.1:8503`. This tunnel publishes Visual Assistant only.
- Started with `docker compose --profile publish up -d cloudflared`. Docker pulled
  `cloudflare/cloudflared:latest` (reported version `2026.10.7`). Backend and
  frontend were healthy; database initializer exited 0; cloudflared registered
  a QUIC connection.
- Cloudflare issued temporary URL
  `https://trend-nashville-traveler-ruled.trycloudflare.com`. Its public
  `/api/health` endpoint returned HTTP 200.
- Compose config validation and `git diff --check` passed. Automated tests were
  not run. At tunnel startup, the backend container had no provider credentials;
  the later credential reload and 502 diagnosis are recorded below. Quick
  Tunnel has no Access policy; anyone with the URL can reach registration.

## Cloudflare request 502 follow-up — 2026-11-09

- The user reported a failed image-generation request. Cloudflare tunnel stayed
  connected and public `/api/health` returned HTTP 200. Backend logs recorded
  `POST /api/images/generate` as HTTP 502, so the tunnel transport was healthy.
- Local ignored `.env` had an OpenAI key, but the running backend container did
  not. The latest failed operation stored a credentials error. The container
  had not been recreated after the local key was added.
- Recreated only the backend with
  `docker compose up -d --no-deps --force-recreate app`. The backend became
  healthy and now receives the key. The key value was not printed.
- A read-only OpenAI `GET /models` returned HTTP 200, and the configured image
  model appeared in the response. No image-generation request was retried.
  Ask the user to retry in the browser; record that result separately.

## Pre-commit verification — 2026-11-09

- Added offline tests for Vietnamese prompt interpretation across generate,
  edit and variation. Verified that the API persists original prompts and the
  image provider receives interpreted text. A prompt-model HTTP failure leaves
  the image provider uncalled and records a failed operation.
- Corrected the roadmap's outdated statement that public publishing still
  awaits a token or domain. Exempted the existing hyphenated standalone secret
  initialization script from Ruff's module-name rule `N999`.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest tests/test_prompt_enhancer.py -q`:
  2 passed.
- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run pytest`:
  29 passed, including 2 development-hook tests.
- Standard isort, Black, flake8 and Ruff checks: passed.
- `npm run build` in `frontend/`: passed; TypeScript and Vite 8.3.6.
- `docker compose --profile publish config --quiet` and `git diff --check`:
  passed.
- Live prompt interpretation, image generation, self-hosted provider and
  browser-driven E2E: not run. The current source image was not deployed.

## UX/UI review — 2026-11-09

- Reviewed the existing React UI with the official `ui-ux-pro-max` skill's UX
  searches for mobile touch targets, form feedback and React semantics. Kept
  the established visual identity instead of applying a new style preset.
- Increased text contrast and readable sizes, added visible keyboard focus,
  larger controls and reduced-motion support. Mobile navigation now has visible
  labels and an accessible logout action.
- Replaced the misleading “Đã lưu tự động” label and static sort chevron. Added
  a library retry state, operation-specific progress text and Vietnamese copy
  for common API errors. Failed creation retains the prompt.
- Guarded asynchronous library and image responses so an old account's pending
  response cannot repopulate the UI after logout or a different login.

### Verification

- `npm ci` in `frontend/`: passed; 25 packages installed, 0 vulnerabilities.
- `npm run build` in `frontend/`: passed; TypeScript and Vite build completed.
- Safari Responsive Design Mode at 375 × 812: auth, empty library, labeled
  bottom navigation, logout action, create form and focus ring inspected.
- Safari at 1440 × 900: create page and sidebar inspected. Local temporary API
  account confirmed missing-provider error appears in Vietnamese; no live model
  call occurred. The temporary backend used a separate `/tmp` database.
- Before integration with the latest `main`, `uv run pytest` passed 30 tests;
  Ruff reported `N999` for the existing hyphenated secret-initializer script.
- After rebasing onto `main` at `70b1018`, `uv run pytest` passed 29 tests.
  The updated base removed obsolete ngrok tests and included its Ruff
  exception. isort, Black, flake8 and Ruff checks all passed.
- `npm run build` and `git diff --check` after the rebase: passed.

Live image generation, image detail with a successful result and browser checks
at other viewport sizes were not run. The temporary backend had no provider
credentials.
## Image count, deletion and Compose deployment — 2026-11-09

- Added a 1–6 image selector. The frontend sends one generation request per
  selected image, in sequence, to avoid holding one proxy request open across
  all provider calls. It reloads the library and reports partial success. Each
  completed image or failed operation remains in its own library record.
- Added owner-scoped `DELETE /api/images/{id}`. Deletion removes the image file
  and hides its record; a SQLite metadata tombstone retains child image links.
  Existing databases receive nullable `deleted_at` during startup. Images that
  are still processing cannot be deleted.
- Updated the charter, AGENTS.md, deployment skill, UI plan, roadmap and ADR
  0009 for the user-authorized count exception to the previous product rule.
- Deployed to the existing `visual-assistant` Docker Compose project on the
  local Docker Desktop host. Its Compose file and ignored `.env` and session
  secret are under `/Users/trieule/Work/visual-assistant`; the rebuilt images
  came from this `feature-sign-in` worktree. No provider credential was printed
  or changed.
- Tagged the old backend/frontend images as `image-studio:rollback-20261109`
  and `image-studio-frontend:rollback-20261109`. Stopped the tunnel and app,
  backed up the persistent volume to the existing ignored host backup directory
  as `image-studio-pre-count-delete-20261109.tgz`, then recreated backend and
  frontend without rebuilding from the older deployment checkout. Restarted
  the Quick Tunnel, which issued a new temporary URL:
  `https://registered-gen-wheels-antibodies.trycloudflare.com`.

Deployment commands (the first build ran from this worktree):

```bash
docker tag image-studio:local image-studio:rollback-20261109
docker tag image-studio-frontend:local image-studio-frontend:rollback-20261109
docker compose build app frontend
docker compose -f /Users/trieule/Work/visual-assistant/compose.yaml --profile publish stop cloudflared
docker compose -f /Users/trieule/Work/visual-assistant/compose.yaml stop app
docker run --rm --user 0 --mount type=volume,src=visual_assistant_image_data,dst=/data,readonly --mount type=bind,src=/Users/trieule/Work/visual-assistant/backups,dst=/backups image-studio:rollback-20261109 tar -czf /backups/image-studio-pre-count-delete-20261109.tgz -C /data .
gzip -t /Users/trieule/Work/visual-assistant/backups/image-studio-pre-count-delete-20261109.tgz
docker compose -f /Users/trieule/Work/visual-assistant/compose.yaml up -d --no-build --no-deps --force-recreate --wait app frontend
docker compose -f /Users/trieule/Work/visual-assistant/compose.yaml --profile publish up -d --no-build --no-deps cloudflared
```

After deployment, corrected the derived-image label for a deleted source,
then ran `npm run build`, `docker compose build frontend` and
`docker compose -f /Users/trieule/Work/visual-assistant/compose.yaml up -d
--no-build --no-deps --force-recreate --wait frontend`. The final frontend
image at that point was `sha256:4ca72c37...`; its deployed asset was
`assets/index-Bp8N832K.js`. The frontend remained healthy, and public health
returned HTTP 200 after recreation.

### Verification

- `uv run pytest tests/test_database.py tests/test_image_studio.py -q`: 20 passed.
  This covers old-DB migration, owner-scoped deletion, file removal, child
  lineage and a deletion storage failure. Multi-image UI behavior has no
  browser automation test; the selector and request loop passed TypeScript
  compilation.
- `uv run pytest`: 32 passed, including 2 development-hook tests.
- `uv run isort --check-only . .codex/hooks/format_python.py`,
  `uv run black --check . .codex/hooks/format_python.py`,
  `uv run flake8 . .codex/hooks/format_python.py`,
  `uv run ruff check . .codex/hooks/format_python.py` and
  `git diff --check`: passed.
- `npm ci`: passed; 25 packages installed and no vulnerabilities reported.
  `npm run build`: passed with TypeScript and Vite 8.3.6.
- `docker compose config --quiet` and
  `docker compose --profile publish config --quiet`: passed.
  `docker compose build app frontend`: passed. New backend image
  `sha256:0a683f5f...` and frontend image `sha256:4ca72c37...` were healthy
  after recreation.
- Stopped-app backup command used `docker run --rm --user 0` with the named
  volume mounted read-only and the host backup directory mounted writable.
  `gzip -t` passed. In the updated container, SQLite `PRAGMA integrity_check`
  returned `ok` and `deleted_at` was present.
- Local `GET /api/health` and `GET /` returned HTTP 200;
  unauthenticated `DELETE /api/images/nonexistent` returned HTTP 401. OpenAPI
  inside the backend lists the DELETE and generate routes. The deployed JS
  asset contains the count selector and delete labels. Public Quick Tunnel
  `GET /api/health` returned HTTP 200.

### Limits and recovery

- Live image generation, browser-driven UI behavior, self-hosted provider and
  LangSmith delivery were not checked. No model call was made for deployment
  verification. Each selected image can incur a provider and prompt-model call.
  Reloading the page during a multi-image action stops later requests; any
  finished operations remain stored.
- Quick Tunnel URL is temporary and has no Cloudflare Access policy. Existing
  backup/restore instructions in `docs/deployment-compose-cloudflare.md` apply.
  For code rollback, retag the two `rollback-20261109` images as `:local` and
  recreate app/frontend with the existing Compose file. A data rollback uses
  the paired archive and a new volume; do not restore over the live volume.

### PR integration follow-up

- Rebasing the feature branch onto `origin/main` brought in the merged UX/UI
  changes. Resolved the generation conflict by retaining session-version
  guards during each of the 1–6 requests, plus the upstream library retry and
  Vietnamese API error handling. The delete action now has the same
  session-version guard. The image count and delete controls meet the newer
  mobile touch-target sizing.
- `uv run pytest`: 32 passed. `npm run build`: passed with 17 transformed
  modules. `git diff --check`: passed.
- Rebuilt and recreated only the frontend again. Final deployed frontend image
  is `sha256:88be60e7...`; asset `assets/index-CaFaOPXc.js` is served locally.
  Frontend is healthy and the Quick Tunnel `/api/health` returned HTTP 200.
  Live model calls and browser interaction remain unverified.
