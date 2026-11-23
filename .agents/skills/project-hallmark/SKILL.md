---
name: project-hallmark
description: Apply Hallmark anti-generic design direction to new Visual Assistant views or explicit Hallmark audits/redesigns, while preserving the existing React product and its real content.
---

# Project Hallmark

Use for every new product view, or when an existing-view Hallmark audit/redesign
is explicitly named. This repository
adaptation is informed by [Nutlope/hallmark](https://github.com/Nutlope/hallmark)
v2.0.0 (MIT). It keeps the useful anti-generic floor without importing the
upstream marketing-site scaffold, themes, Together AI calls, CSS stamp, or
`sloplint` as a project dependency.

## Routing

- New view or new product surface: use Hallmark to choose a distinct direction
  and one clear job, then use `project-ui` to preserve product behavior.
- Existing view named in a Hallmark audit/redesign request: use Hallmark plus
  `project-design-taste`; retain content, wiring, auth, library and image flows.
- Ordinary visual polish or restyle without Hallmark named: use
  `project-design-taste` and do not start a Hallmark run.
- Functional UI change: use `project-ui`; Hallmark is not a functional test.

## Project floor

- Route colors, fonts, spacing and motion through the existing CSS tokens.
- Keep `:focus-visible`, keyboard use, reduced-motion behavior and 320px
  reflow intact. Avoid `transition: all`, layout-jump animation and horizontal
  overflow.
- Use real product copy, prompts, statuses, thumbnails and controls. Never add
  invented metrics, testimonials, logos, decorative proof or fake data.
- Give each screen one clear job and primary action. Avoid generic hero copy,
  purple-blue gradients, emoji icons, nested cards and decorative effects with
  no product purpose.
- Preserve the charter: auth, library, create 1–6, detail, edit, variation,
  delete, download, loading, partial batch and error recovery.

## Handoff and evidence

Planner records material, audience, user job, tone, signature interaction,
affected states and preserved behavior. Coding records the chosen direction
and keeps the existing React/CSS architecture. Testing uses
`project-browser-evaluation` and Playwright at desktop and mobile widths; it
checks real interactions, focus, long Vietnamese content, loading/errors and
overflow. A visual browser pass does not prove backend isolation, deployment or
live provider behavior.
