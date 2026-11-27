# ADR 0013 — Bound GPT-Image-2.6 render complexity

Date: 2026-11-27
Status: Accepted
Extends: ADR 0005 and ADR 0006

## Context

Read-only LangSmith traces on 2026-11-27 showed the image provider consumed
122.18 seconds of a 125.58-second generation. Prompt interpretation consumed
3.32 seconds. All seven observed runs used OpenAI `gpt-image-2.6-sunburst`.

## Decision

Send server-configured `complexity=medium` for OpenAI GPT-Image-2.6 Sunburst and
Flare generation, edit and variation requests. Accept only `low`, `medium` or
`high` in `IMAGE_COMPLEXITY`; use `high` to restore the previous default tradeoff.
Do not send the parameter to older models or OpenAI-compatible endpoints.
Keep PNG output, storage, owner isolation, tracing redaction and success rules.

## Alternatives considered

- Optimize prompt interpretation: its 3.32-second share in the slowest trace is
  small beside the 122.18-second provider call.
- Increase request concurrency: reduces batch completion time, but not the
  provider time for one image.
- Change model or output format: could reduce latency, but also changes image
  characteristics beyond the measured bottleneck adjustment.

## Consequences

Medium complexity targets the provider step that dominates latency. Complex
layouts or dense text may lose detail or accuracy. The exact latency reduction
and image-quality impact require a post-rollout LangSmith comparison.

## Review triggers

- Post-rollout traces show no useful latency reduction or unacceptable output
  quality; set `IMAGE_COMPLEXITY=high` while revisiting the choice.
- Another image model gains a documented complexity parameter.
