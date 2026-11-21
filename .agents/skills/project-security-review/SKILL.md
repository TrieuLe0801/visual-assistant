---
name: project-security-review
description: Review Visual Assistant security boundaries from source and safe local evidence for explicit audit or focused security-review requests.
---

# Project Security Review

Use for an explicit security review, not routine feature verification. Read
`AGENTS.md`, the active charter, relevant accepted ADRs and
`docs/security-audit-2026-11-10.md` when the reviewed boundary overlaps it.

Define actor, protected image/prompt/account/action, entry point, expected
control and observable effect. Trace each reachable path through auth, owner
scope, validation, provider handling, SQLite/file storage and response. Check
alternate routes to the same effect. Report a vulnerability only with a
reachable failure and concrete impact. Separate confirmed findings, open
checks and disproved candidates; missing best practice alone is not evidence.

Prioritize owner-scoped image queries and file reads, edit/variation source
ownership, deletion, signed sessions, registration controls, rate limits,
provider response bounds, and storage failure handling as applicable. Preserve
server-only provider settings. Keep API keys, passwords, session secrets,
prompts and image bytes out of logs and metadata-only traces. Treat provider
output as untrusted; validate image content before storage. Use fake providers
and isolated local data for safe probes. Do not read secrets, call live models,
or infer deployed behavior from source alone.

For each finding, give affected path, principal, violated control, impact,
source and observed evidence, smallest useful fix, and verification limits.
