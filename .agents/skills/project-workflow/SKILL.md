---
name: project-workflow
description: Coordinate every repository change through planner, coding, testing, and deployment-readiness agents; use for feature, code, configuration, documentation, and product-behavior work.
---

# Project Workflow

Use this workflow for every requested repository change: feature work, bug
fixes, refactors, configuration, documentation, and product behavior. Do not
use it for pure questions or status explanations that do not change files.

The primary Codex session coordinates four project agents in this order:

1. `planner` reads the required project records and current worktree, then
   defines one structured goal. Include acceptance criteria, owned file scope,
   dependencies, checks, evidence boundaries, and risks. Planner does not edit.
2. `coding` receives the planner goal and owns the implementation scope. It
   preserves existing user changes, records a coding goal, maps each planned
   criterion to achieved, partial, or blocked, and reports changed files and
   checks. It does not broaden scope silently.
3. `testing` receives both planner's goal and coding's report. It checks the
   actual artifact against every acceptance criterion and coding claim, runs
   deterministic relevant checks, and reports failures with reproduction steps.
   It must not weaken tests or invent live-provider evidence.
4. `deploying` uses `project-deployment` to review release readiness, rollback,
   secrets, storage, health, and live-evidence limits. It may prepare release
   steps, but deploys only when the user explicitly requests deployment.

The primary session passes these handoffs explicitly, waits for each role before
starting the next, and owns integration. If testing finds a gap, send a bounded
correction back to `coding`, then rerun testing and deployment readiness. Do not
declare completion until the artifact, verification result, and required project
records are updated. Keep offline tests, deployed health checks, and live model
checks separate.

## Handoff format

Use these labels so later agents can audit the chain:

- `Planner goal`: outcome, acceptance criteria, file scope, checks, risks.
- `Coding goal`: implementation outcome and status for each planner criterion.
- `Testing result`: evidence for each planner criterion and coding claim,
  commands, failures, and unrun checks.
- `Deployment readiness`: target, backup/rollback, configuration and health
  evidence, release blockers, and whether deployment was authorized.

The skill is implicitly discoverable. `AGENTS.md` makes this sequence mandatory
for repository changes even when automatic skill selection is unavailable.
