# Learning Log — AI image studio MVP

Date: 2026-11-08
Status: Current

## Hallmark and taste routing — 2026-11-23

- Added project-local `project-hallmark`, adapted from `Nutlope/hallmark` v2.0.0
  (MIT). It applies only to new views or explicit Hallmark audit/redesign
  requests. It preserves the image-studio charter and omits upstream themes,
  marketing scaffolds, Together AI calls, CSS stamps and `sloplint` dependency.
- Routed Hallmark through `project-ui`, `project-design-taste`,
  `project-browser-evaluation`, and planner/coding/testing agent instructions.
  Taste remains default for ordinary visual polish. No runtime UI changed.
- Installed upstream `hallmark` separately in `/Users/trieule/.codex/skills/`;
  personal skills remain outside repository and become available next session.

### Verification

- `quick_validate.py` for `project-hallmark`, `project-ui`,
  `project-design-taste` and `project-browser-evaluation`: passed.
- Agent TOML parse and targeted source-reference checks: passed.
- `git diff --check`: passed. Runtime, browser, provider and deployment checks:
  N/A; this change only updates workflow instructions.

- Correction cycle 1: aligned Hallmark routing so every new product view uses
  Hallmark, while existing-view audit/redesign uses it only when explicitly
  named. Replaced inaccurate Playwright availability wording with “repository
  Playwright” wording. Targeted routing search, TOML parse and `git diff
  --check` passed.

## UI/UX studio redesign — 2026-11-24

Coding goal: improve the existing React studio's library, prompt creation and
detail hierarchy while preserving auth, image workflows and the 1–6 selector.
The library now groups count, ordering and next-step guidance. The create form
groups prompt guidance and options, and shows semantic batch progress. Detail
groups follow-on edit and variation actions. `ux-polish.css` applies a warm
editorial visual system and responsive layout. No backend, dependency or
provider code changed. Research sources and acceptance mapping are in
`docs/ui-plan.md`.

Correction cycle 2 added client-side prompt search and status filtering to the
library, a distinct no-match state, and a focused Playwright scenario. Search
and filter reset on logout. A follow-up mobile fix sets `.create-layout` to one
column below 760px so the prompt form remains usable at 320px.

Testing result: all six planner criteria remain present in source. Library,
create and detail hierarchy changed; auth and stored-output behavior are
preserved. Search and filter use loaded records and the original prompt.
Rendered layout and browser behavior are verified below; live provider and
deployment behavior remain separate evidence.

Verification:

- `uv run pytest -q`: passed, 42 tests.
- `uv run isort --check-only . .codex/hooks/format_python.py`: passed.
- `uv run black --check . .codex/hooks/format_python.py`: passed.
- `uv run flake8 . .codex/hooks/format_python.py`: passed.
- `uv run ruff check . .codex/hooks/format_python.py`: passed.
- `git diff --check`: passed.
- `npm ci`: passed, 29 packages installed.
- `npm run build`: passed.
- `npm run test:browser -- --workers=1`: passed, 14 desktop/mobile tests,
  including 320px layout and library search/filter.
- `docker compose config --quiet`: passed in deployment-readiness review.
- Running stack, tunnel, public health and live provider: not run for this
  source revision. Deployment was not requested or performed.

## Commit and PR preparation — 2026-11-23

- Fixed a malformed planner-agent instruction that split the repository
  Playwright guidance after `Do not assume`.
- Audited the 17 intended changed paths for scope, secrets, real user prompts,
  and image files. No credentials, real prompts, or user images were found;
  changes remain limited to workflow docs, skills, agents, Playwright setup and
  deterministic browser tests.

### Verification

- Five project skills passed `quick_validate.py`; five TOML files (`config.toml`
  and four agents) parsed successfully. `git diff --check`: passed.
- `npm run build` and `npm run test:browser -- --workers=1` in `frontend/`:
  passed; TypeScript/Vite build passed and 12 desktop/mobile Chromium tests
  passed. API calls remain mocked, so provider and deployed behavior are not
  proven.
- `uv run pytest`: 42 passed. isort, Black, flake8 and Ruff checks passed.
- Branch, commit, push and PR creation are handled by the primary session after
  this correction. No deployment performed.

## UI visual refresh — 2026-11-23

- Applied image-first gallery hierarchy (three-column desktop, two-column tablet/phone), larger readable typography, warmer surfaces, translucent navigation chrome, and clearer action contrast in `frontend/src/ux-polish.css`.
- Preserved auth, library, create 1–6 images, detail, edit, variation, delete, download, loading, empty, partial-batch, and error behaviors. No provider/model/size controls added.
- Responsive rules cover desktop, tablet, 320px phone layouts; primary controls retain 44px minimum touch targets, visible focus, and reduced-motion handling.
- Research used Figma's 2026 bold typography direction, Adobe's human/organic 2026 direction, and WCAG 2.2 reflow, focus, and target-size guidance.

### Verification

- `npm ci --offline` and `npm run build` in `frontend/`: passed after CSS refresh; Vite emitted the production bundle and TypeScript completed.
- `uv run pytest -q`: 42 passed. `uv run isort --check-only . .codex/hooks/format_python.py`, `uv run black --check . .codex/hooks/format_python.py`, `uv run flake8 . .codex/hooks/format_python.py`, and `uv run ruff check . .codex/hooks/format_python.py`: passed.
- `git diff --check`: passed after the gallery-density correction.
- Local frontend `http://127.0.0.1:8088/` returned HTTP 200 before the refresh. CUA browser attachment returned `browser access host is unavailable`; rendered interaction and screenshot comparison remain unverified.

## GitHub Actions CI/CD — 2026-11-21

- Added hosted CI for locked Python tests and style checks, frontend build, and
  default/publish Compose validation.
- Added manual main-only CD for a protected production environment and a
  dedicated self-hosted Compose runner. Deployment backs up the paired volume,
  checks health, and attempts image rollback on failure.
- No runner, environment approval, deployment, provider call, or public health
  check was available in this change. See ADR 0012 and the deployment guide.
- Correction: CD stages source into persistent `DEPLOY_DIR`, excludes `.env`,
  `.secrets/`, backups and target marker, and requires the existing
  `visual-assistant` Compose project and volume before Compose runs. Checkout
  no longer persists its token, and staging excludes `.git/`.
  `bash -n scripts/deploy-compose.sh`, YAML parsing, `docker compose config
  --quiet`, `docker compose --profile publish config --quiet`, and
  `git diff --check` passed. `uv run pytest -q`: 42 passed. Standard isort,
  Black, flake8 and Ruff checks passed. Frontend `npm ci --offline` and
  `npm run build` passed. Deployment remains unverified.

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

## Session revocation security fix — 2026-11-21

- Confirmed logout replay: a captured signed cookie remained accepted after
  `/api/auth/logout` because logout only cleared the browser cookie.
- Added SQLite-backed session revocation with SHA-256 token hashes and expiry;
  authenticated routes reject revoked tokens, including after app restart.
- Added regression coverage for replay and independent-session behavior. No
  token value or secret is persisted.
- Follow-up review found arbitrary logout cookies could create unbounded rows.
  Logout now revokes only a valid unexpired signed token; invalid logout still
  clears the browser cookie and returns 204. Revocation cleanup runs on valid
  revocation, not on every authenticated request.
- Focused `uv run pytest tests/test_image_studio.py -q`: 23 passed. Full `uv run
  pytest -q`: 42 passed. Offline replay probe returned 401 on account, image
  list, image file and generation endpoints after logout; restart and a separate
  session passed. A 100-cookie invalid logout probe created no revocation rows.
- isort, Black, flake8, Ruff, frontend `npm run build` and `git diff --check`:
  passed. No live provider, container rollout or browser E2E check was run.

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

### Security audit — 2026-11-10

- Reviewed API auth, owner-scoped image access, provider adapters, image
  validation, Compose/Nginx and locked dependencies. Findings, remediation and
  residual risk are recorded in `docs/security-audit-2026-11-10.md` and ADR 0010.
- `uv run --python 3.11 pytest -q`: 40 passed, 1 LangSmith warning for missing
  hosted API key. `uv run --python 3.10 pytest -q`: 40 passed, same warning.
  Focused security tests: 32 passed after provider response caps were added.
- `uv run --python 3.11 isort --check-only . .codex/hooks/format_python.py`,
  `uv run --python 3.11 black --check . .codex/hooks/format_python.py`,
  `uv run --python 3.11 flake8 . .codex/hooks/format_python.py`,
  `uv run --python 3.11 ruff check . .codex/hooks/format_python.py`,
  `uv lock --check` and `git diff --check`: passed.
- `npm run build` passed; `npm audit --omit=dev` found 0 vulnerabilities.
  `npm audit` including development dependencies also found 0 vulnerabilities.
  `uvx bandit -q -r src` found no issues.
  `docker build --target app -t image-studio:security-audit .` passed. Isolated
  container check reported Python 3.11.18, Pillow 13.0.0 and app factory import.
- `pip-audit` on the locked Python 3.11 production dependency export found no
  known vulnerabilities. Python 3.10 export reported 39 Pillow 12.3.0
  advisories; app compatibility still passes on 3.10. Do not deploy 3.10 for
  untrusted image processing while this remains unresolved.
- No public tunnel, real account, live provider, browser or production rollout
  was exercised. The existing Compose deployment remains on the previous image.
- Docker Scout on the original Bookworm app image reported 121 findings (16
  high). Switched runtime to Python 3.11 slim Trixie, applied Debian upgrades
  and removed uv/pip/setuptools/wheel from the final stage. Final arm64 image
  scan: 27 findings (0 critical, 0 high, 1 medium, 26 low). The medium
  finding is Debian `tar` CVE-2025-45582; the scanner lists no fixed version.
  Rebuilt the final image and verified Python 3.11.18, Pillow 13.0.0 and app
  factory import inside an isolated container. The container's TestClient
  startup and `GET /api/health` returned 200 with `Cache-Control: no-store`.

### Python 3.10 and Pillow security closure — 2026-11-10

- Pillow 13.0.0 is the patched release for the prior Pillow 12.3.0 advisories,
  but it dropped Python 3.10 support. ADR 0011 raises project support to
  Python `>=3.11`. Updated `.python-version`, `pyproject.toml`, `uv.lock`,
  formatter/linter targets, project instructions and deployment guidance.
  The previous Python 3.10 environment capture remains historical.
- `uv lock` resolved 59 packages; `uv sync --locked` selected CPython 3.11.16
  and Pillow 13.0.0. `uv run --python 3.10 --locked ...` failed as expected
  because the interpreter does not meet `requires-python >=3.11`. The lockfile
  no longer contains Pillow 12.3.0.
- Focused `uv run pytest tests/test_image_studio.py tests/test_prompt_enhancer.py
  -q`: 24 passed. After updating UTC handling for the Python 3.11 Ruff target,
  `uv run pytest tests/test_database.py -q`: 4 passed and full `uv run pytest
  -q`: 40 passed.
- `uv run isort --check-only . .codex/hooks/format_python.py`, Black, flake8,
  Ruff, `uvx bandit -q -r src`, `uv lock --check`, Compose config and
  `git diff --check`: passed. `npm run build`: passed.
- Locked production dependency export audited with `pip-audit`: no known
  vulnerabilities. `docker build --target app -t image-studio:security-audit .`
  passed. An isolated container reported Python 3.11.18, Pillow 13.0.0 and
  `GET /api/health` HTTP 200 with `Cache-Control: no-store`. Docker Scout on
  the final arm64 image again reported 27 OS findings, none high or critical.
- No live provider, public tunnel or existing Compose stack was exercised.
  The Docker image used for the previous deployment remains active until a
  separate rollout.

### Registration pause and Compose rollout — 2026-11-10

- Added `REGISTRATION_ENABLED=false` as the runtime default. The UI reads
  `/api/auth/registration-status` and hides registration while disabled; the
  registration API returns HTTP 403. Login behavior remains available.
- Set the ignored local `.env` value to false. No credential value was read or
  written to tracked files.
- Ran isort, Black, flake8 and Ruff checks, frontend TypeScript/Vite build,
  Compose publish-profile config validation and `git diff --check`; all passed.
  Automated tests were not run for this rollout.
- Tagged the prior app and frontend images for rollback. Stopped the tunnel and
  app, then created `backups/image-studio-pre-registration-pause-2026-11-10.tgz`
  from the persistent volume. `gzip -t` passed; archive size was 34.4 MiB.
- Built the app and frontend images, then started both with Compose. Database
  initializer exited 0; app and frontend became healthy. Restarted the
  Cloudflare Quick Tunnel after local checks.
- Local and public `/api/health` returned HTTP 200. Local and public
  `/api/auth/registration-status` returned `{"enabled":false}`. Registration
  POST returned HTTP 403; dummy login returned HTTP 401, confirming the login
  route remains active without using a real account. Frontend root returned
  HTTP 200. SQLite `PRAGMA integrity_check` returned `ok`; existing account
  record remained present.
- Current temporary Quick Tunnel URL:
  `https://amsterdam-emotions-zones-familiar.trycloudflare.com`. Quick Tunnel
  has no Access policy; anyone with the URL can reach login. No real account
  login, browser session or live image operation was tested. Docker Scout was
  not rerun on the newly built images; the latest recorded scan has 27 OS
  findings, none high or critical.

## Codex skills and agents review — 2026-11-14

- Reviewed the active charter, status, ADRs, environment records, project
  tree, source/test entry points and the existing Codex workflow. Preserved
  pre-existing edits to deployment, registration, application and UI files.
- Removed the `manager` agent because the primary Codex session already
  coordinates work. Kept `planner`, `coding`, `testing` and `deploying` with
  their existing model assignments; both model IDs are present in the local
  Codex model catalog.
- Removed `codex-workflow-transfer`, which serves occasional cross-repository
  migration, and `project-change-verification`, whose checks already appear in
  `AGENTS.md`. Kept and narrowed `project-deployment` for release-specific
  single-host storage, secrets, tunnel and evidence checks. Updated all four
  remaining agent instructions to preserve user edits and report failures
  without weakening tests or hardcoding application behavior.
- Updated `AGENTS.md`, the workflow guide and ADR 0001 to match the retained
  files. No application code or test assertions were changed for this review.

### Verification

- `codex debug models | jq -r '.models[].slug' | rg
  '^(gpt-6-sol|gpt-5\\.6-luna)$'`: both configured model IDs found.
- Parsed `.codex/config.toml` and four agent TOMLs with `tomllib`; model and
  role assertions passed.
- `uv run --with PyYAML python
  /Users/trieule/.codex/skills/.system/skill-creator/scripts/quick_validate.py
  .agents/skills/project-deployment`: passed. The first attempt with system
  `python3` could not run because PyYAML was not installed there; no skill
  validation result was claimed from that attempt.
- `uv run pytest`: 39 passed, 1 failed, both before and after workflow edits.
  Failing test: `tests/test_deployment_config.py::test_session_secret_file_overrides_environment`.
  It deletes `SESSION_COOKIE_SECURE` from the process environment, then
  `Settings.from_env()` calls `load_dotenv()` and loads the ignored local
  `.env`, where `SESSION_COOKIE_SECURE=false`. The assertion expects the
  default `True`; observed value is `False`. No test, application behavior or
  local setting was changed to force a pass.
- `uv run isort --check-only . .codex/hooks/format_python.py`,
  `uv run black --check . .codex/hooks/format_python.py`,
  `uv run flake8 . .codex/hooks/format_python.py`,
  `uv run ruff check . .codex/hooks/format_python.py`, frontend
  `npm run build` and `git diff --check`: passed.
- `uv lock --check`, `docker compose --profile publish config --quiet` and
  JSON parsing of `docs/progress/roadmap-progress.json`: passed.
- The pre-existing worktree changes `compose.yaml` to a named Cloudflare Tunnel
  with an external network, while README, the deployment guide and status
  still describe Quick Tunnel. This review did not claim that the new tunnel
  is deployed or rewrite the in-progress deployment records.
- Live provider, browser and deployed-environment checks: not run for this
  workflow-only change.

## Named Cloudflare Tunnel documentation — 2026-11-14

- The user confirmed the domain now routes through a named Cloudflare Tunnel
  and requested removal of the temporary tunnel workflow. The existing
  `compose.yaml` and running `visual-assistant-cloudflared-1` already use
  `tunnel --no-autoupdate run --token-file /run/secrets/cloudflare_tunnel_token`.
  No container or secret was changed in this documentation update.
- Replaced the temporary tunnel instructions in README, the deployment guide,
  current status, roadmap and ADR 0007 with the `aliter.app` named-tunnel path.
  Updated the deployment agent's instructions and the active security wording.
  Kept earlier tunnel events in this log as historical evidence.
- Updated `docs/progress/roadmap-progress.json` to record the named tunnel
  milestone and current public health check. Cloudflare Access policy was not
  verified; no claim is made that it is enabled.

### Verification

- `docker inspect --format '{{json .Config.Cmd}}' visual-assistant-cloudflared-1`:
  the running container uses the named-tunnel token file.
- `docker compose config --quiet` and
  `docker compose --profile publish config --quiet`: passed.
- `curl -fsS https://aliter.app/api/health`: HTTP 200. Public and local
  frontend root HTML had matching SHA-256
  `45fc73f9979622967b5b01042c02d64a356c37174769171ded5122c045dfe24f`.
- `uv run pytest`: 39 passed, 1 failed in
  `test_session_secret_file_overrides_environment`, matching the prior
  worktree result. The ignored local `.env` sets `SESSION_COOKIE_SECURE=false`;
  no assertion, runtime behavior or local configuration was changed to force
  a pass.
- isort, Black, flake8, Ruff, frontend `npm run build`, `uv lock --check`,
  JSON parsing of the roadmap progress file and `git diff --check`: passed.
- No app image rebuild, container recreation, provider call or browser E2E
  check was needed for this documentation and workflow update.

## Required Codex project workflow — 2026-11-14

- Added `.agents/skills/project-workflow/` for every requested repository
  change, including feature, code, configuration and documentation work.
- Updated `AGENTS.md` to require planner, coding, testing and deploying agents
  in sequence. The planner defines the goal and acceptance criteria. Coding
  reports implementation against them. Testing checks both the planner goal
  and coding report against the artifact. Deploying reviews release readiness
  using `project-deployment`; rollout requires a separate user request.
- Updated the coding and testing role instructions, workflow guide, project
  status and ADR 0001 to match. Pure questions and status requests are exempt.

### Verification

- `env UV_CACHE_DIR=/private/tmp/visual-assistant-uv-cache uv run --with
  PyYAML python /Users/trieule/.codex/skills/.system/skill-creator/scripts/quick_validate.py
  .agents/skills/project-workflow`: passed (`Skill is valid!`). TOML parsing
  of project config and four agents, plus YAML parsing of both skills: passed.
  The first validator attempt without the temporary uv cache could not access
  the sandboxed default cache; rerunning with the writable cache passed.
- `uv run pytest`: 39 passed, 1 failed in
  `tests/test_deployment_config.py::test_session_secret_file_overrides_environment`.
  The ignored local `.env` sets `SESSION_COOKIE_SECURE=false`, while the test
  expects the default `True`. This matches the prior worktree result. Neither
  the test nor runtime settings were changed to mask it.
- `uv run isort --check-only . .codex/hooks/format_python.py`,
  `uv run black --check . .codex/hooks/format_python.py`,
  `uv run flake8 . .codex/hooks/format_python.py`,
  `uv run ruff check . .codex/hooks/format_python.py`,
  `npm run build` in `frontend/`, `docker compose config --quiet`,
  `docker compose --profile publish config --quiet` and `git diff --check`:
  passed. An initial `npm run build` at the repo root found no `package.json`;
  the frontend build passed from the correct directory.
- Deployment review: no application image, Compose runtime, SQLite volume or
  secret changed. Existing guide records paired-volume backup and rollback.
  No deployment was requested or performed. Docker socket access was denied,
  and local/public health endpoints were unreachable from this review, so no
  current runtime health claim was made. Live-provider and browser checks were
  not run for this workflow-only change.

## Compose network decoupling — 2026-11-15

- Removed the archived product's external Docker network from `compose.yaml`.
  Compose config connects `cloudflared` and `frontend` to the default network;
  tunnel origin remains `http://frontend:80`.
- Updated the deployment guide to describe the project-scoped default network.
  Kept the named tunnel route, service names, volume, secrets and `aliter.app`
  unchanged. Historical archive and baseline records remain unchanged.

### Verification

- `docker compose config --quiet`: passed.
- `docker compose --profile publish config --quiet`: passed.
- Active configuration, source, skill and current operations-document search
  found no archived product network or identifier. Historical `docs/archive/`
  and baseline records were excluded by design.
- `uv run pytest`: 40 passed.
- `uv run isort --check-only . .codex/hooks/format_python.py`,
  `uv run black --check . .codex/hooks/format_python.py`,
  `uv run flake8 . .codex/hooks/format_python.py`,
  `uv run ruff check . .codex/hooks/format_python.py` and
  `npm run build` in `frontend/`: passed.
- `git diff --check`: passed.
- Runtime health, deployment, browser behavior and live provider checks were
  not run.

### Deployment readiness

- All four existing `backups/*.tgz` archives passed `gzip -t`. This checks
  archive integrity, not whether their contents restore successfully.
- `docker ps` and `docker inspect visual-assistant-cloudflared-1` could not
  access the Docker socket in this session (`permission denied`). Running
  container state and local/public health were not rechecked.
- No rollout was requested or performed. Before a later rollout, retain the
  prior images and a paired-volume backup; use the deployment guide for
  rollback and health checks.

## Repository skill and agent adaptation — 2026-11-21

- Compared the source `grounded-travel-planner` development skills, five agent
  definitions, `AGENTS.md`, and `.codex/config.toml` with this repository's
  active charter, UI plan, source, checks, and four-role project workflow. The
  source repository remained read-only.
- Added project-owned `requirement-clarification`, `project-ui`,
  `project-browser-evaluation`, and `project-security-review` skills. Reworked
  scope and examples for React/TypeScript/CSS, FastAPI, SQLite, local image
  files, owner isolation, server-selected image providers, and actual UI flows.
- Folded the source delivery-orchestrator's useful Goal Card, call-path,
  minimal-change, and evidence guidance into the existing `project-workflow`.
  Kept the target's required planner/coding/testing/deploying sequence and
  model assignments. Adapted the four agent instructions and updated
  `AGENTS.md` and `docs/codex-workflow.md` routing and skill inventory.
- Did not import the source research/coordinator/deployer roles, travel product
  policies, Auth0/PostgreSQL/Tavily/LangGraph assumptions, Tailwind design
  system, or Playwright command. The target has no committed browser test
  runner; browser evaluation uses available tools and records observed evidence.
  No application runtime behavior, dependencies, or architecture decision
  changed. No roadmap item closed.

### Verification

- `quick_validate.py` through `uv run --with PyYAML python` on all six skills:
  passed. The first broad directory loop met two leftover untracked skill
  directories without `SKILL.md` and exited 1; the corrected loop selected
  only actual skills and passed.
- `tomllib` parsed `.codex/config.toml` and all four agent TOMLs; `json` parsed
  `docs/progress/roadmap-progress.json`; PyYAML parsed six skill frontmatters
  and two existing `agents/openai.yaml` files. Local references in 12 touched
  instruction/skill files resolved. An initial reference probe treated the
  `.codex/agents/*.toml` glob as a literal file and exited 1; the corrected
  glob-aware probe passed.
- `uv run pytest`: 40 passed. `uv run isort --check-only .
  .codex/hooks/format_python.py`, `uv run black --check .
  .codex/hooks/format_python.py`, `uv run flake8 .
  .codex/hooks/format_python.py`, `uv run ruff check .
  .codex/hooks/format_python.py`, and `npm run build` in `frontend/`: passed.
- Browser, deployed-container, and live-provider checks: N/A for instruction
  and skill changes. No deployment or PR requested or performed.

## Repository skill and agent refresh — 2026-11-23

- Rechecked `/Users/trieule/Work/grounded-travel-planner/.codex` because the
  requested `~/grounded-travel-planner/.codex` path is absent. Kept the Image
  Studio adaptation: four agents and six project skills; no travel-specific
  Auth0, PostgreSQL, Tavily, Tailwind or Playwright rules were copied.
- Added Goal Card fields for scope, exclusions and commit/push/deploy intent;
  status, branch and upstream preflight; bounded two-cycle correction loop; and
  explicit non-pass reasons to project workflow, agent instructions and the
  portable workflow guide. No application or architecture change.

### Verification

- `uv run --with PyYAML python /Users/trieule/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/project-workflow`: passed.
- `uv run python` TOML parse of `.codex/config.toml` and four agent files: passed; roles are `planner`, `coding`, `testing`, `deploying` with models `gpt-6-sol`, `gpt-5.6-luna`, `gpt-5.6-luna`, `gpt-5.6-luna`.
- Six project skill directories were present; source-term review found only explicit warnings that Tailwind/Playwright are unavailable, with no travel-product rules copied. `git diff --check`: passed.
- `uv run pytest`: 42 passed. `uv run isort --check-only . .codex/hooks/format_python.py`: passed. `uv run black --check . .codex/hooks/format_python.py`: passed. `uv run flake8 . .codex/hooks/format_python.py`: passed. `uv run ruff check . .codex/hooks/format_python.py`: passed.
- An initial `npm run build` at the repository root failed because there is no
  root `package.json`. `npm ci --offline` and `npm run build` in `frontend/`:
  passed.
- Browser, container and live-provider checks: N/A because this change only updates Codex instructions. No deployment or PR requested or performed.

## Visual design taste skill — 2026-11-23

- Added project-local `project-design-taste`, adapted from taste-skill 2.5.1
  (MIT, Leonxlnx/taste-skill). It covers visual briefs, coherent typography,
  color, layout, real product content, restrained motion and browser evidence.
- Updated UI, browser, planner, coding and testing handoffs. The skill routes
  only for visual polish or redesign; existing React/CSS, product charter,
  image-library workflows and deployment boundaries remain authoritative.
- Excluded source starter HTML, assets, scripts, finish gate, marketing layout
  rules and company-site assumptions. No application redesign performed.
- Installed the upstream `design-taste-frontend` skill from
  `Leonxlnx/taste-skill` in the personal Codex skills directory. The repository
  keeps its smaller Image Studio adaptation for portable agent handoffs.

### Verification

- `quick_validate.py` passed for `project-design-taste`, `project-ui` and
  `project-browser-evaluation`.
- Frontend build and browser runner checks remain recorded in this log; no live
  provider or deployment check applies to this skill-only change.

## Browser acceptance runner — 2026-11-23

- Added locked `@playwright/test` dependency, `npm run test:browser`, dedicated
  Vite web server on port 4173, desktop/mobile Chromium projects, and ignored
  Playwright reports. Browser tests mock every `/api/**` route before page
  navigation and abort unexpected requests.
- Added deterministic coverage for disabled registration, login/library,
  partial six-image creation, detail prompt/download, library retry, logout
  clearing, and mobile overflow. Updated browser/UI skills with the real runner
  and handoff rules.

### Verification

- `npm run build`: passed.
- `npx playwright install chromium`: passed; Chromium downloaded.
- `uv run --with PyYAML python .../quick_validate.py` for each changed skill:
  passed.
- Initial `npm run test:browser` worker discovery hung because Node 24 loaded
  the TypeScript config through Playwright's experimental ESM restart and the
  spec imported the `Page` type as a runtime export. The spec now uses a type-
  only import and the script sets `PW_DISABLE_TS_ESM=1`.
- `npm run test:browser -- --project=chromium-mobile --grep "mobile layout" --workers=1`:
  passed (1 test at 320px viewport).
- `npm run test:browser -- --workers=1`: passed (12 tests; desktop and mobile
  Chromium). The suite starts Vite automatically on port 4173, mocks and
  aborts unexpected `/api/**` calls, and checks mobile document overflow.
- Corrected a strict locator failure in the six-image test by targeting the
  submit button. Removed duplicate `@playwright/test` package keys and pinned
  the package-lock entry. Backend proxy and live-provider checks: N/A.
- Follow-up review found stale wording in `.codex/agents/planner.toml`,
  `.codex/agents/coding.toml`, `.codex/agents/testing.toml` and
  `docs/codex-workflow.md` that still says Playwright is absent. This is a
  documentation consistency failure requiring a bounded instruction correction;
  browser artifacts themselves pass.

### Correction cycle 1

- Replaced stale Playwright-absent wording with the repository
  `npm run test:browser` desktop/mobile Chromium workflow. Kept Tailwind absent
  and live-provider/deployed claims separate.
- TOML parse, targeted wording search and `git diff --check`: passed.

### Correction cycle 2

- Corrected one remaining contradictory phrase in `docs/codex-workflow.md` to
  state that the repository Playwright suite exists. Targeted search and
  `git diff --check`: passed.

### Correction cycle 3

- Replaced the remaining Playwright availability wording in the testing agent
  with “repository Playwright” and added explicit Hallmark routing for new
  product views. TOML parse, targeted wording search and `git diff --check`:
  passed.

## Provider rejection diagnostics — 2026-11-24

- Traced image edit failures to the OpenAI-compatible adapter's 400/422 branch.
  It discarded structured provider fields and returned one generic message.
- Added bounded parsing for allow-listed error codes and parameters. Source
  image, edit capability and unsupported request parameter failures now return
  safe actionable messages without copying provider text.
- Unknown or malformed error bodies retain the generic message. Success,
  credential, rate-limit and server-error mappings remain unchanged.

### Verification

- `uv run pytest tests/test_image_studio.py -q`: passed (28 tests).
- `uv run pytest -q`: passed (47 tests).
- `npm ci --offline && npm run build` in `frontend/`: passed.
- `uv run isort --check-only . .codex/hooks/format_python.py`: passed.
- `uv run black --check . .codex/hooks/format_python.py`: passed.
- `uv run flake8 . .codex/hooks/format_python.py`: passed.
- `uv run ruff check . .codex/hooks/format_python.py`: passed.
- `git diff --check`: passed.
- Live provider edit: not run; current checkout has no provider credentials.
- Deployment: not run. Existing Compose target health returned HTTP 200 locally;
  public health could not be checked because DNS resolution failed.
