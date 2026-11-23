---
name: project-design-taste
description: Apply restrained visual direction to Visual Assistant React/CSS polish or redesign work, with coherent type, color, layout, real product states, and browser inspection; do not use for functional fixes or deployment.
---

# Project Design Taste

Use only when request changes visual hierarchy, typography, color, layout,
motion, or responsive composition. Route functional UI fixes to `project-ui`
alone. For every new product view, pair this skill with `project-hallmark`; for
an existing view, pair it only when user names a Hallmark audit/redesign. This
adaptation draws principles from `taste-skill 2.5.1` (MIT,
Leonxlnx/taste-skill); it does not copy starter HTML, assets, scripts, finish
gate, marketing structure, or company-site assumptions.

## Brief before code

Planner states affected view, user task, primary action, existing CSS tokens,
real content and product states, and whether work is polish or redesign. Keep
auth, library, create 1–6, detail, edit, variation, delete, download, loading,
partial batch and error recovery intact.

## Visual direction

- Choose one visual system. Define type scale, color roles, spacing rhythm,
  surfaces, borders, focus treatment and button hierarchy before styling.
- Give each screen one clear priority. Align content edges and keep hierarchy
  readable at 1440, 1024, 768 and 320px widths.
- Use real product copy, prompts, statuses, thumbnails and controls. Do not add
  invented testimonials, metrics, addresses, photos or marketing sections.
- Prefer CSS and existing assets. Use restrained hover/focus feedback and short
  entrance motion only where it clarifies state. Respect reduced motion.
- Keep images purposeful. Avoid empty frames, generic dashboards, excessive
  rounded cards and effects without product value.

## Handoff and evidence

Coding preserves interaction inventory and hands changed states to testing.
Testing uses `project-browser-evaluation` for rendered checks: desktop/mobile
Chromium, keyboard focus, 320px overflow, loading/error/empty states and long
Vietnamese copy. Separate visual evidence from build, backend, deployment and
live-provider evidence. Report observed artifact and missing baseline.
