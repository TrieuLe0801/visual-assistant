# ADR 0010 — Security guards for public image studio

Date: 2026-11-10
Status: Accepted
Amends: ADR 0005 and ADR 0007
Python 3.10 compatibility decision superseded by ADR 0011.

## Context

The Compose application can be reached through a public Cloudflare Tunnel. Account
creation and image generation can consume host and provider resources. The
previous session-secret fallback was predictable outside Compose, and Pillow
12.3.0 has published security advisories.

## Decision

- Require an explicit session secret of at least 24 UTF-8 bytes, reject the
  former sample value, and default cookies to Secure. Local HTTP development
  must explicitly opt out of Secure cookies.
- Start the ASGI app through a factory so a missing secret fails at startup
  without making test imports depend on deployment environment.
- Persist atomic fixed-window safety limits in SQLite for registration, login
  and image operations. Use global and per-email/per-user keys. Hash normalized
  emails before storing rate-limit keys. Return HTTP 429 with `Retry-After`.
- Temporarily disable new registrations by default with `REGISTRATION_ENABLED=false`.
  Keep the registration API gated and expose a non-secret status for the UI so
  only existing accounts can sign in while the pause is active.
- Return `Cache-Control: no-store` and defensive headers on all `/api/`
  responses. Apply the same password verification work to unknown accounts.
- Stream and cap provider JSON responses before parsing them: 30 MiB for image
  responses and 128 KiB for prompt-model responses.
- Use the Python 3.11 slim Trixie base and Pillow 13.0.0 in the deployment image.
  Upgrade Debian packages during the build and copy only the installed app
  environment from a separate build stage. Remove pip, setuptools and wheel
  from the runtime image. Keep Python 3.10
  compatibility with Pillow 12.3.0 for development; do not deploy that runtime
  for untrusted image processing while its advisories remain unresolved.

## Consequences

- Limits are shared across the single SQLite-backed app and survive restarts.
  An attacker can still exhaust a global window and deny legitimate work.
  These safety caps are not a billing quota or account admission control.
- Existing sessions remain valid if the deployment keeps its file-backed
  secret. Operators must provide a unique secret for any new deployment.
- Provider responses above the caps fail the operation before image storage.
  A valid 20 MiB image encoded in base64 fits within the 30 MiB JSON cap.
- Python 3.10 remains functionally supported, but its Pillow 12.3.0 branch has
  a known dependency risk. Revisit when a supported patched release exists.
- The final arm64 runtime image still has Debian package advisories with no
  current fix. Rebuild and rescan after base-image or Debian security updates.

## Review triggers

- Public traffic needs stricter abuse control or per-IP limits at a trusted
  edge, with care for proxies and shared IPs.
- Multiple app hosts require a shared rate-limit store.
- A patched Pillow version supports Python 3.10, or project support moves to
  Python 3.11+.
