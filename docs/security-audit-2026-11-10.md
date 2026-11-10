# Security audit — 2026-11-10

Scope: repository FastAPI API, React client, SQLite and local image storage,
provider adapters, Docker/Compose/Nginx configuration and locked Python/npm
dependencies. This was a source review and offline verification; no public
tunnel, real user data or live provider was exercised.

## Confirmed findings and remediation

| Severity | Finding | Evidence and fix |
|---|---|---|
| High | A known default session secret could sign arbitrary user sessions in non-Compose deployments. | `src/image_studio/config.py:164` previously used a public sample. It now requires an explicit unique secret, rejects that sample, and the ASGI factory fails startup if absent. |
| High | Unrestricted public registration and image calls could exhaust host capacity or incur provider charges. | `src/image_studio/app.py:150` and `src/image_studio/database/repository.py:162` now enforce SQLite-backed atomic global/per-identity fixed-window limits. Tests cover exhaustion and persistence. |
| Medium | Pillow 12.3.0 has published advisories. | `Dockerfile:26` and `pyproject.toml:10` move deployment to Python 3.11 with Pillow 13.0.0. A locked Python 3.11 dependency export had no known advisories in `pip-audit`. See residual risk below. |
| Medium | The previous Bookworm runtime image carried many OS and build-tool advisories. | `Dockerfile:26` now uses Debian Trixie, upgrades installed OS packages and copies only the app environment from a build stage. Runtime pip, setuptools, wheel and uv are absent. Docker Scout findings fell from 121 to 27. |
| Medium | Image-provider and prompt-model responses could be buffered without a byte bound. | `src/image_studio/ai/openai_compatible.py:128` and `src/image_studio/ai/prompt_enhancer.py:83` now stream and reject responses above 30 MiB and 128 KiB respectively before JSON parsing. Offline tests exercise both limits. |
| Medium | Private API responses and image files lacked a no-store directive. | `src/image_studio/app.py:108` sets `Cache-Control: no-store` on `/api/` responses; tests cover account and file responses. |
| Low | Unknown emails skipped password-hash verification, creating a timing difference. | `src/image_studio/app.py:181` verifies against a dummy scrypt hash when the account is absent; test confirms this path. |

## Controls reviewed without a confirmed finding

- Owner filtering is applied to library records, file reads, edit/variation
  sources and deletion. Existing tests cover cross-account access.
- Provider URLs and credentials come from server configuration. The adapter
  accepts base64 image content and does not fetch provider-supplied URLs.
- Image validation accepts PNG/JPEG/WebP, rejects mismatched signatures and
  limits file size and pixels. Session cookies are HttpOnly and SameSite Strict.
- No tracked secret file was found in the repository search. npm audit reported
  zero known vulnerabilities.

## Residual risk and limits

- Python 3.10 resolves Pillow 12.3.0. `pip-audit` reported 39 advisories for
  that version, with 13.0.0 listed as the fix; Pillow 13 drops Python 3.10.
  The app only accepts PNG/JPEG/WebP, so the audit count does not mean all 39
  advisories are reachable here. Do not expose a Python 3.10 deployment to
  untrusted image data. [Pillow 13 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html), [Pillow advisories](https://github.com/python-pillow/Pillow/security/advisories).
- Fixed global windows can be exhausted deliberately, causing temporary 429s
  for legitimate users. Quick Tunnel has no Access policy. A trusted edge and
  account admission controls are still needed before broad public use.
- Docker Scout still reports 27 findings in the final arm64 runtime image:
  0 critical, 0 high, 1 medium and 26 low. The medium finding is in Debian
  `tar` (CVE-2025-45582), with no fixed package in the scanner report; the app
  does not invoke `tar` for HTTP requests. Operators use it for backups. The
  remaining findings require later base-image or Debian updates and review.
- This audit did not include a dynamic penetration test, browser automation,
  live provider call or production rollout. Offline tests do not prove those
  environments safe.

## Verification

- `uv run --python 3.11 pytest -q`: 40 passed, 1 LangSmith missing-key warning.
- `uv run --python 3.10 pytest -q`: 40 passed, same warning.
- `uv run --python 3.11 isort --check-only . .codex/hooks/format_python.py`,
  Black, flake8 and Ruff: passed.
- `uv lock --check`, `git diff --check`: passed.
- `npm run build`: passed. `npm audit`: zero vulnerabilities.
- `uvx bandit -q -r src`: no findings.
- `docker build --target app -t image-studio:security-audit .`: passed. Isolated
  image import/factory check reported Python 3.11.18 and Pillow 13.0.0. Isolated
  container startup and `GET /api/health` returned HTTP 200 with `no-store`.
- `docker scout cves` on the original Bookworm app image: 121 findings (16
  high). Final Trixie multi-stage runtime: 27 findings (0 high). Both scans
  analyzed local arm64 images. The final report is summarized above.
- Python 3.11 locked production dependency export: `pip-audit` found no known
  vulnerabilities. Python 3.10 export: 39 Pillow 12.3.0 advisories.
