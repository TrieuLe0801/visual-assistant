---
name: project-deployment
description: Prepare and verify deployment work for this FastAPI and React image studio when the user requests a release or deployment.
---

# Project Deployment

Use this skill for deployment planning, configuration, release checks, or an
explicit deployment request. Follow the repository read order in `AGENTS.md`.
Inspect existing container, hosting, and release files before adding a platform
or deployment convention.

## Project constraints

- Set `SESSION_SECRET` through the target platform's secret store before
  non-development deployment.
- Keep provider API keys and other credentials out of source, database, API
  responses, and logs.
- Keep SQLite and the image volume persistent. The documented design supports
  one application host; multi-host deployment needs a separate storage decision.
- Establish SQLite and image-volume backup and restore steps before production
  data is stored.
- Preserve owner-scoped image and file access, provider configuration on the
  server, and the UI restriction against provider/model/image parameter choice.
- Live provider checks need valid credentials and an active endpoint. Record
  those checks separately from offline tests and build results.

## Deployment workflow

1. Identify the requested target and environment from the user request or
   existing repository configuration. Do not choose a hosting provider by
   assumption.
2. Inspect the deployment path, required secrets, persistent storage, health
   checks, and rollback or recovery options. Report missing decisions after
   completing independent inspection.
3. Run the checks required by the task and project instructions. Separate build,
   offline, live-provider, and deployed-environment evidence.
4. Make only the requested deployment changes. Perform an external or production
   deployment only when the user explicitly asks for it.
5. Record the target, exact commands, observed outcome, and operational limits.
   Never report a deployment as successful without direct evidence.
