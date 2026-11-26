---
name: project-workflow
description: Coordinate every repository change through research, planning, coding, testing, and deployment-readiness agents; use for feature, code, configuration, documentation, and product-behavior work.
---

# Project Workflow

Use this workflow for every requested repository change: feature work, bug
fixes, refactors, configuration, documentation, and product behavior. Do not
use it for pure questions or status explanations that do not change files.

Before handoff, primary session records a compact Goal Card: objective, user
outcome, acceptance criteria, scope and exclusions, verification, and explicit
commit/push/deploy intent. Missing product decisions are recorded as unresolved
decisions for the primary session to ask; absent commit or push intent means no commit or
push.

The primary Codex session coordinates five project agents in this order:

1. `researcher` reads required records and current worktree, surveys relevant
   code and primary sources when useful, compares options, recommends an
   approach, and reports evidence, assumptions, risks, and unresolved decisions.
   Researcher does not edit.
2. `planner` consumes the Research result and reads the required project records
   and current worktree, then defines one implementation plan. Use the Research
   result as source of evidence; research only material evidence gaps. Include
   acceptance criteria, owned file scope, dependencies, checks, evidence
   boundaries, and risks. For UI work, include a design brief and interaction
   inventory using `project-ui`. If a user decision blocks acceptance, carry it
   into the handoff and ask the primary session; continue independent work.
   Planner does not edit.
3. `coding` receives the Research result and planner goal and owns the implementation scope. It
   preserves existing user changes, records a coding goal, maps each planned
   criterion to achieved, partial, or blocked, and reports changed files and
   checks. It does not broaden scope silently.
4. `testing` receives the Research result, planner goal and coding's report. It checks the
   actual artifact against every acceptance criterion and coding claim, runs
   deterministic relevant checks, and reports failures with reproduction steps.
   For browser acceptance, use `project-browser-evaluation`. It must not weaken
   tests or invent live-provider evidence.
5. `deploying` uses `project-deployment` to review release readiness, rollback,
   secrets, storage, health, and live-evidence limits. It may prepare release
   steps, but deploys only when the user explicitly requests deployment.

The primary session passes these handoffs explicitly, waits for each role before
starting the next, and owns integration. If testing finds a gap, send a bounded
correction back to `coding`, then rerun testing and deployment readiness. Do not
declare completion until the artifact, verification result, and required project
records are updated. Keep offline tests, deployed health checks, and live model
checks separate.

Run preflight before edits: inspect `git status --short`, branch and upstream,
then identify unrelated dirty files. Preserve them. Allow at most two bounded
coding correction and testing retest cycles; report any remaining blocker.

Trace defects through the affected path and confirm a focused failure before a
fix when reproducible. Reuse existing code and installed tools before adding
dependencies or layers. Preserve validation, owner isolation, data-loss
handling, accessibility, and explicit acceptance. Run narrow relevant checks,
then the full available suite required by `AGENTS.md`; label unavailable checks
`N/A`. A documentation-only edit does not require unrelated browser or live
provider checks. Do not create a platform Goal for routine repository work.

## Handoff format

Use these labels so later agents can audit the chain:

- `Research result`: evidence, options, recommendation, assumptions, risks,
  unresolved decisions, and evidence limits.
- `Planner goal`: outcome, acceptance criteria, file scope, checks, risks.
- `Coding goal`: implementation outcome and status for each planner criterion.
- `Testing result`: evidence for each planner criterion and coding claim,
  commands, failures, and unrun checks.
- `Deployment readiness`: target, backup/rollback, configuration and health
  evidence, release blockers, and whether deployment was authorized.

Every check report marks `passed`, `failed`, `skipped`, or `not run`, with a
reason for each non-pass result. Review final diff against Goal Card and project
contracts. Stage or commit only explicit files when authorized; push only an
authorized feature branch after required checks pass.

The skill is implicitly discoverable. `AGENTS.md` makes this sequence mandatory
for repository changes even when automatic skill selection is unavailable.
