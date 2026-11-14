# Portable Codex development workflow

This repository keeps its Codex development workflow in Git:

| Path | Purpose |
|---|---|
| `AGENTS.md` | Project rules and required reading |
| `.codex/config.toml` | Coordinator model and agent concurrency |
| `.codex/agents/*.toml` | Planner, coding, testing, and deployment roles with model assignments |
| `.agents/skills/project-deployment/` | Release-specific checks for this single-host image studio |
| `.codex/hooks.json`, `.codex/hooks/format_python.py` | Python edit hook |
| `pyproject.toml`, `uv.lock` | Development tools and locked dependencies |

The primary session coordinates work; no separate manager agent is needed.
Development agents are separate from the app's image-provider adapters. The
coordinator and planner use `gpt-6-sol`. Coding, testing, and deployment use
`gpt-5.6-luna`. `AGENTS.md` holds the verification sequence and evidence rules;
the deployment skill holds release-specific checks.

For Codex configuration and custom-agent schema, see the [configuration
reference](https://developers.openai.com/codex/config-reference/) and
[subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Another machine, same repository

1. Clone the repository and open it as a trusted Codex project. Project config
   and custom agents load in trusted project sessions. Review the hook before
   enabling it through Codex's hook trust flow.
2. Install Codex and `uv`, then run `uv sync`. Confirm configured models are
   available to the signed-in account. Run `codex debug models` to inspect the
   local Codex model catalog.
3. Set up credentials in ignored local environment files. Do not transfer
   `.env`, personal Codex config, plugin cache, or credentials through Git.
4. Check that Codex discovers the four agents and one repository skill. Run
   the verification commands in `AGENTS.md`.

Personal skills in `~/.agents/skills/` or `~/.codex/skills/`, including
`caveman`, are not part of this repository. Install them separately on the
other machine if wanted. Plugin-provided skills require the plugin there.
Personal instructions such as an absolute `~/.codex/RTK.md` reference also
need separate setup; they are not repository files.

## Another repository

Copy only relevant `.codex/agents/` and `.agents/skills/` folders. Copy
`.codex/config.toml` after checking coordinator model and concurrency needs.
Confirm each assigned model appears in the destination account's Codex model
catalog.
Rewrite `AGENTS.md` from the destination's actual decisions. Copy the hook
only for a compatible Python project with its formatting tools installed.
Remove product-specific rules, source paths, and verification commands that do
not apply. Inventory the result and run the destination's own checks before
committing it.

## Skill checks

Use `skill-creator`'s `quick_validate.py` for each changed skill. Validate the
agent TOML files and check that instructions match the active project records.
Record the commands, findings, and limits in the current learning log.
