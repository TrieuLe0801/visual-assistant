---
name: project-browser-evaluation
description: Evaluate Visual Assistant browser flows and responsive UI with observed interaction evidence; use when browser behavior or visual acceptance is requested.
---

# Project Browser Evaluation

Read `AGENTS.md`, the planner goal, `docs/ui-plan.md`, and affected UI/API paths.
For visual polish or redesign, read `project-design-taste` and verify its brief
against the rendered artifact. For every new product view, also read
`project-hallmark`; for an existing view, read it only when user names a
Hallmark audit/redesign, then check its floor and preserved product behavior.
Use Playwright for deterministic rendered checks. Run `npm run test:browser`
from `frontend/`; `playwright.config.ts` starts a dedicated Vite server on
port 4173 and runs desktop and mobile Chromium projects. Tests route every
`/api/**` request before navigation and abort unexpected calls, so browser
checks do not require a backend, provider, credentials, or live data.

For offline interaction checks, isolate test accounts and mock image providers
or API responses. Exercise login, server-disabled registration, library and
detail navigation, create count, edit, variation, delete, download, and error
recovery only as relevant to the change. Verify that success follows stored
API output and an earlier session's response cannot repopulate a new session.
Never treat a mocked provider result as live generation evidence.

Keep mocks deterministic and complete. Add focused tests under
`frontend/tests/browser/`; use role and label locators. A passing mocked browser
test proves UI behavior only, not backend isolation or provider quality.

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
