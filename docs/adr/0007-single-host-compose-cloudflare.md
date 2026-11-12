# ADR 0007 — Single-host Compose deployment with Cloudflare Tunnel

Date: 2026-11-08
Status: Accepted
Extends: ADR 0005
Amended: Replaced ngrok publish service with Cloudflare Quick Tunnel on 2026-11-09;
added an optional named-tunnel overlay for the Grounded Travel Planner ingress on 2026-11-12.

## Context

The image studio needs a local container build and a public HTTPS entrypoint for
trusted testing. The storage design assumes one application host, one SQLite
database and one image volume. No production hosting provider is selected.

## Decision

- Build separate React/Nginx frontend and Python/FastAPI images in a
  multi-stage Dockerfile. Install locked backend dependencies with uv.
- Use Docker Compose on one Docker Desktop host. Bind the frontend only to
  `127.0.0.1:${FRONTEND_PORT:-8088}`; keep the backend on the private Compose
  network. The operator can set `FRONTEND_PORT` when that host port is in use.
- Add a one-shot `database` service to initialize the SQLite schema before the
  backend starts. SQLite remains embedded, not a network service.
- Run `cloudflared` as a separate Compose service under the optional `publish`
  profile. Use Cloudflare Quick Tunnel and forward to `frontend:80` on the
  private Compose network. Quick Tunnel needs no account token or custom domain.
- Treat the Quick Tunnel URL as temporary. It can change after restart and has
  no uptime guarantee. Use a remotely-managed named tunnel and Cloudflare Access
  before sharing a stable custom domain.
- Keep the default Quick Tunnel deployment self-contained. For the shared-host
  Grounded Travel Planner deployment, provide an optional Compose overlay that
  runs the existing connector as a remotely-managed named tunnel and attaches it
  to the planner's external ingress network. Keep its tunnel token in a local
  Compose secret file.
- Store SQLite and image files together in a named Docker volume. Stop the app
  before a paired backup of the whole volume. Restore into a new volume before
  switching the app to it.
- Give the app `SESSION_SECRET` through a file-backed Compose secret. Keep
  provider and LangSmith credentials in ignored local configuration.
- Mark session cookies Secure because public traffic uses HTTPS. Add an
  application health check for `/api/health`.

## Alternatives considered

- Keep ngrok: rejected because its configured endpoint was already online and
  publishing failed with `ERR_NGROK_334`.
- Bind the app to all host interfaces: rejected because the tunnel can use the
  private Compose network.
- Run multiple app replicas: rejected because SQLite and the local image volume
  do not have a multi-writer design.
- Put `cloudflared` in the app image: rejected because the tunnel needs a
  separate lifecycle.
- Introduce cloud object storage or a managed database: deferred until a
  multi-host deployment or stronger durability requirement exists.

## Consequences

- The Docker host and `cloudflared` container must stay online for the temporary
  public URL to work.
- Quick Tunnel has no Cloudflare Access policy by default. Anyone with the URL
  can reach registration and login. App data remains owner-scoped, but signup
  limits and generation quotas are not implemented. Use only for trusted tests.
- A Quick Tunnel URL is not suitable for a stable domain or production entrypoint.
- The named-tunnel overlay requires the Grounded Travel Planner Compose stack to
  create its external ingress network before the connector starts.
- A healthy container does not prove live image-provider or LangSmith calls.
- The named volume and `.secrets/` directory require separate operating and
  backup practices. Changing the session secret invalidates sessions.

## Review triggers

- The app moves to a managed host or multiple instances.
- A stable custom domain, Cloudflare Access policy or public signup is required.
- Storage needs automatic scheduled backups or recovery objectives.

## References

- [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets)
- [uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/)
