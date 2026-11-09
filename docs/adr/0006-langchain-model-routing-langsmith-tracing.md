# ADR 0006 — LangChain image model routing and LangSmith tracing

Date: 2026-11-08
Status: Accepted
Extends: ADR 0005

## Context

The image studio already has a typed image-provider interface and a single
server-configured provider/model. The administrator needs a way to maintain
several model choices and select one without exposing model controls to users.
Image API operations are not interchangeable with chat-model calls. Tracing
must not copy private prompts or image bytes to an observability service.

## Decision

- Keep the existing image API adapter behind the provider-independent contract.
- Use LangChain Core `RunnableConfigurableAlternatives` to route generate, edit
  and variation operations to the server-selected provider/model profile.
- Define profiles in `IMAGE_MODEL_CATALOG`; select one at startup with
  `IMAGE_ACTIVE_MODEL`. Preserve `IMAGE_PROVIDER`/`IMAGE_MODEL` when no catalog
  is configured. Credential and endpoint variables stay server-side.
- Use LangSmith `@traceable` for the complete image operation. Record operation,
  source presence, result status, record ID, provider and model. Remove prompt,
  source bytes, result bytes, owner ID and credentials from trace inputs/outputs.
- Disable automatic LangChain runnable tracing around image calls to prevent
  a child run from capturing raw image data. LangSmith remains opt-in through
  `LANGSMITH_TRACING` and `LANGSMITH_API_KEY`.
- Do not add a user-facing or public model-switch endpoint. An administrator
  changes `IMAGE_ACTIVE_MODEL` and restarts the backend.

## Alternatives considered

- Replace the image adapter with a chat-model integration: rejected because
  image generation/edit contracts and returned bytes differ from chat output.
- Trace raw prompts and images: rejected because the library is private and
  metadata suffices for operation timing, failure and model routing checks.
- Add a runtime admin API: deferred because the MVP has no admin role or
  control plane.

## Consequences

- LangChain Core and LangSmith become runtime dependencies. The uv lockfile
  records exact versions.
- Model switching needs a backend restart, so in-flight requests continue on
  the previous instance until it stops.
- Metadata-only traces cannot be used to inspect prompt quality or image
  content. Failed operations still retain the safe error and status in SQLite.
- Live image-provider and LangSmith delivery checks require credentials and
  endpoints; offline tests do not prove remote behavior.

## Review triggers

- Administrators need live switching without a restart.
- Provider contracts diverge from the selected OpenAI-compatible image API.
- Trace policy changes to include user content with explicit consent.

## References

- [LangChain configurable alternatives](https://reference.langchain.com/python/langchain-core/runnables/base/RunnableSerializable/configurable_alternatives)
- [LangSmith traceable functions](https://reference.langchain.com/python/langsmith/run_helpers/traceable)
- [LangSmith tracing context](https://reference.langchain.com/python/langsmith/run_helpers/tracing_context)
