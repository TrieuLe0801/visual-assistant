---
name: project-browser-evaluation
description: Evaluate Visual Assistant browser flows and responsive UI with observed interaction evidence; use when browser behavior or visual acceptance is requested.
---

# Project Browser Evaluation

Read `AGENTS.md`, the planner goal, `docs/ui-plan.md`, and affected UI/API paths.
Use an available browser automation tool for rendered checks. The frontend has
`npm run build` but no committed Playwright dependency, browser test directory,
or `test:browser` script; do not claim those checks exist. Add a browser test
runner only when the requested acceptance justifies that dependency and the
project adopts it.

For offline interaction checks, isolate test accounts and mock image providers
or API responses. Exercise login, server-disabled registration, library and
detail navigation, create count, edit, variation, delete, download, and error
recovery only as relevant to the change. Verify that success follows stored
API output and an earlier session's response cannot repopulate a new session.
Never treat a mocked provider result as live generation evidence.

For visual work, inspect rendered states at representative phone, tablet and
desktop widths. Compare matching before/after states when a baseline exists.
Check clipping, labels, focus, long Vietnamese prompts, image placeholders,
loading/errors, touch targets and reduced motion. A screenshot alone cannot
prove a control works; interact with affected controls.

For live evaluation, record target URL, revision, browser, account type,
scenario, expected result and observed result. Keep credentials, real user
prompts, generated images and session artifacts out of Git. Report each check
as passed, failed, skipped or not run with exact command or tool, result and
reason for non-pass. Separate browser UI, backend owner isolation, deployed
health and real provider behavior.
