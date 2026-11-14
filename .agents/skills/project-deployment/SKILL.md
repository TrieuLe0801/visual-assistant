---
name: project-deployment
description: Prepare or verify a release of this image studio using its Compose deployment, persistent data, and Cloudflare tunnel.
---

# Project Deployment

Use for deployment planning, configuration, release checks, or an explicit
deployment request. Follow `AGENTS.md` and the current deployment guide in
`docs/deployment-compose-cloudflare.md`. Inspect `compose.yaml` and the actual
target before changing deployment files; the tunnel configuration may change
between releases.

## Project constraints

- Preserve the paired SQLite and image volume on the single supported host.
  Check backup and restore evidence before a change that may affect stored data.
- Supply session and tunnel secrets from ignored files or the target secret
  store. Never put provider credentials in tracked files or command output.
- Check authentication, owner-scoped data access, and server-side provider
  settings after deployment changes that touch those paths.
- Record live provider calls separately from offline tests, builds, and health
  checks. A healthy service does not prove image generation works.

## Deployment workflow

1. Identify the target from the request and current repository configuration.
2. Inspect secrets, storage, health checks, and rollback or recovery before a
   release. Resolve missing target details before dependent work.
3. Run the relevant project checks. Report failed checks without changing tests
   or hardcoding application behavior to force a pass.
4. Deploy when the user requests deployment. Record the target, exact commands,
   observed outcome, and limits in the current learning log.
