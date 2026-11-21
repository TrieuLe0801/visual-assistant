---
name: project-ui
description: Plan and change Visual Assistant's React interface while preserving image-library workflows, accessibility, and observable UI behavior.
---

# Project UI

Use for interface audits, polish, and requested redesigns. Read `AGENTS.md`,
`docs/project-charter.md`, `docs/ui-plan.md`, and relevant ADRs. Inspect
`frontend/src/App.tsx`, the affected CSS, and API responses before editing.

Planner records a compact brief: affected view, user task, existing components
and styles, available real content, acceptance criteria, and changed files.
Inventory links, forms, handlers, navigation, focus, and loading/error/empty
states. For visual changes, capture comparable baseline evidence if the app is
available; otherwise state the gap. Keep an audit read-only, a polish change
within its named surface, and a redesign within the requested product scope.

Preserve login for existing accounts and server-controlled registration state.
Keep the library, create, detail, edit, variation, delete, source relationship,
and download flows consistent with the charter. Show the user's original prompt
and operation status. A creation action selects 1–6 images; provider, model,
image size, and aspect ratio remain server-side. Show success only after the API
reports stored output. Keep failed and partial batch results distinct. Do not
display a source image as a new result after failure. Clear account data on
logout and ignore stale responses from a prior session.

Reuse current React components, CSS tokens and Vietnamese copy patterns. The
app uses React, TypeScript and CSS; do not assume Tailwind, a component library,
or a multilingual switch exists. Keep controls keyboard usable, visibly
focused, and responsive. Check labels, touch targets, contrast, long prompts,
empty libraries, loading and error recovery, and reduced motion when affected.

Coding hands the brief and interaction inventory to testing. When acceptance
depends on rendered behavior or appearance, use `project-browser-evaluation`.
Separate build, browser, backend, deployed, and live-provider evidence.
