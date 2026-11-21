# ADR 0012: GitHub Actions CI and gated Compose CD

Date: 2026-11-21
Status: Accepted

## Context

The image studio runs as a single Docker Compose deployment with SQLite and
image files in one named volume. A release needs a paired backup and a rollback
path. Pull-request code must never run with Docker access to the deployment
host.

## Decision

Use GitHub-hosted Actions for read-only CI on pull requests and pushes to
`main`. CI installs Python with `uv --locked`, runs the project checks, builds
the frontend, and validates both Compose profiles.

Use a separate manual `workflow_dispatch` job for deployment. It only accepts
`main`, runs on a dedicated self-hosted runner label, and requires a protected
`production` environment. The deployment script preserves host `.env`,
`.secrets/`, and the named data volume; creates a stopped-app backup; builds and
health-checks the release; and restores prior image tags if health fails.

## Consequences

CI is reproducible and does not need provider credentials. CD remains gated by
human approval and runner administration. Self-hosted runner compromise can
expose the deployment host, so it must not process pull requests. Backup
archives still need off-host retention, and live provider behavior remains a
separate check.
