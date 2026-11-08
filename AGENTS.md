@/Users/trieule/.codex/RTK.md

Use the installed `caveman` skill at `full` level by default in Codex replies.
Keep Vietnamese when the user writes Vietnamese. Preserve technical accuracy.
If the user asks for normal style or disables caveman, follow that request.

## AI Image Studio — Codex Instructions

### Project boundary

- This repository is an independent FastAPI and React learning/product project.
- The MVP creates, edits and varies images from prompts, then saves them to a
  personal library. It is not a booking or social-sharing product.
- Treat repository Markdown as durable project context. Browser localStorage,
  chat history and assumptions are not project evidence unless recorded here.

### Read before changes

Before editing code or project decisions, read these files in order:

1. `PROJECT_STATUS.md`
2. `docs/project-charter.md`
3. the current file under `docs/learning-log/`
4. relevant records under `docs/adr/`, when they exist
5. `docs/experiments/baseline-environment.md` for environment-dependent work

### Architecture

- Use FastAPI for typed backend routes and React + TypeScript for the web UI.
- Keep image-provider calls behind a typed, provider-independent interface.
- Support OpenAI API and an OpenAI-compatible self-hosted endpoint.
- Configure provider, model, endpoint and credentials on the server through
  environment variables. Do not expose these settings to end users.
- Use SQLite for account and image metadata. Use a local volume for image files.
- Keep every image query and file read scoped to the authenticated owner.
- Keep work bounded. Report unsupported provider operations clearly.

### Product invariants

- Never report success before the provider returns a valid image and storage
  completes.
- Keep prompts, operation status, metadata and source/derived relationships.
- User A must never read or change user B's image or prompt.
- Never put API keys, session secrets, passwords or provider credentials in the
  database, API response or logs.
- Do not let users choose provider, model, image size, aspect ratio, count or
  other generation parameters.
- Preserve the workflow outcomes defined in `docs/project-charter.md`.

### Working agreements

- The primary Codex session uses `gpt-6-sol` to coordinate project work.
  Project agents use `gpt-6-sol` for `manager` and `planner`, and
  `gpt-5.6-luna` for `coding`, `testing` and `deploying`. Assign bounded work
  when specialist roles improve the result. Coordinate shared-file edits.
- These Codex development agents are separate from the app's runtime. See
  `docs/adr/0001-python-development-tooling.md`.
- Use `codex-workflow-transfer` for migration to another repository or machine.
  Use `project-change-verification` for project checks and `project-deployment`
  for deployment work. See `docs/codex-workflow.md` for the portable file set
  and local setup.
- Support Python `>=3.10`. Use `uv` for dependencies, environments and command
  execution. Commit `uv.lock` after dependency changes.
- Use `pytest`, isort, Black, flake8 and Ruff for Python checks. Use TypeScript
  build for frontend checks. Keep network/model calls out of unit tests.
- Use Docker Desktop for local containers when needed; prefer arm64 images on
  the MacBook M1.
- Store secrets only in ignored environment files. Never commit credentials,
  prompts from real users or image files from real users.
- Do not claim tests, providers or live behavior exist until executable
  artifacts and verification evidence exist.
- Update `PROJECT_STATUS.md`, the current learning log and
  `docs/progress/roadmap-progress.json` when a roadmap item is complete.
- Add or update an ADR when changing a confirmed architecture decision.
- Run the narrowest relevant checks, then the available full suite. If no
  executable check exists, report it as `N/A`.

Once the Python project exists, use these standard verification commands:

```bash
uv run pytest
uv run isort --check-only . .codex/hooks/format_python.py
uv run black --check . .codex/hooks/format_python.py
uv run flake8 . .codex/hooks/format_python.py
uv run ruff check . .codex/hooks/format_python.py
```

### Completion evidence

A task is complete only when its durable artifact exists and its verification
result is recorded. A checked box in `docs/roadmap.html` alone is not evidence.
