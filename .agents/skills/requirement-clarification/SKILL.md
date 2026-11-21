---
name: requirement-clarification
description: Clarify an unresolved Visual Assistant project decision or run a user-requested deep requirements interview before planning dependent work.
---

# Requirement Clarification

Use for development requirements, not a prompt submitted to the image studio.
Planner researches the request and reports missing decisions to the primary
session. The primary session asks the user and records answers.

- **Focused mode:** Ask only decisions that change scope, acceptance, an
  irreversible effect, or a confirmed project contract. Continue independent
  work. Resolve ordinary implementation choices from the charter, ADRs and code.
- **Deep interview:** Use only when the user asks for an exhaustive requirements
  discussion. Group independent decisions, then ask dependent questions after
  their prerequisites are answered. Stop when material branches have answers or
  explicit exclusions.

Before asking, inspect the current goal, `PROJECT_STATUS.md`, active charter,
relevant ADRs, affected code and earlier explicit decisions. Do not ask the
user for facts available in the repository. Keep questions short, state useful
options and tradeoffs, and use the user's language. Record the answer and any
assumption in the planner goal; update durable project records when a decision
changes ongoing context. Do not demand confirmation for already authorized
reversible work.
