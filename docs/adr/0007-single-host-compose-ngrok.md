# ADR 0007 — Single-host Compose deployment with ngrok

Date: 2026-11-08
Status: Accepted
Extends: ADR 0005
Amended: Compose frontend, ngrok and SQLite initializer services

## Context

The image studio needs a local container build and a temporary public HTTPS
entrypoint. The existing storage design assumes one application host and one
SQLite database plus image volume. No cloud hosting provider was selected.

## Decision

- Build separate React/Nginx frontend and Python/FastAPI images in a
  multi-stage Dockerfile. Install locked backend dependencies with uv.
- Use Docker Compose on one Docker Desktop host. Bind the frontend only to
  `127.0.0.1:8000`; keep the backend on the private Compose network.
- Add a one-shot `database` service to initialize the SQLite schema before the
  backend starts. SQLite remains embedded in the app, not a network service.
- Run ngrok as a separate Compose service under the optional `publish` profile.
  It forwards to the frontend container and reads Basic Auth from a Compose
  secret. The token and optional URL come from ignored `.env`.
- Store SQLite and image files together in a named Docker volume. Stop the app
  before a paired backup of the whole volume. Restore into a new volume before
  switching the app to it.
- Give the app `SESSION_SECRET` through a file-backed Compose secret. Keep
  provider and LangSmith credentials in ignored local configuration. Protect
  the ngrok endpoint with Basic Auth in addition to the app's own login.
- Do not pass the ngrok token to the backend or frontend containers. The
  earlier host CLI launcher remains an optional manual fallback.
- Mark session cookies Secure because public traffic uses ngrok HTTPS. Add an
  application health check for `/api/health`.

## Alternatives considered

- Bind the app to all host interfaces: rejected because ngrok only needs local
  access to the app port.
- Run multiple app replicas: rejected because SQLite and the local image volume
  do not have a multi-writer design.
- Put ngrok in the app image: rejected because the tunnel needs a separate
  container, account configuration and lifecycle.
- Introduce cloud object storage or a managed database: deferred until a
  multi-host deployment or stronger durability requirement exists.

## Consequences

- The Docker host and ngrok container must stay online for the public URL to
  work.
- The ngrok account's domain may already be occupied by another endpoint;
  publishing must use an available domain or stop the existing owner-managed
  endpoint.
- A healthy container does not prove live image-provider or LangSmith calls.
- The named volume and `.secrets/` directory require separate operating and
  backup practices. Changing the session secret invalidates sessions.

## Review triggers

- The app moves to a managed host or multiple instances.
- Public access needs a stable custom domain or a stronger access policy.
- Storage needs automatic scheduled backups or recovery objectives.

## References

- [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets)
- [uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [ngrok domains](https://ngrok.com/docs/gateway/domains)
