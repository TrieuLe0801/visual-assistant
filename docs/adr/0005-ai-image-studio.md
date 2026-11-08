# ADR 0005 — AI image studio product scope and storage

Date: 2026-11-08
Status: Accepted
Supersedes: ADR 0004 for product scope and runtime behavior

## Context

The user replaced the travel-planning product with a webapp for image
generation. Users authenticate with email and password, generate images from
prompts, edit saved images, create variations and reopen the prompt/image
history in a personal library.

## Decision

- Build a FastAPI backend with a React/TypeScript frontend.
- Use email/password accounts and owner-scoped image metadata/file access.
- Persist account data, prompt, operation status, metadata and source/result
  relationships in SQLite. Store image files on a local volume.
- Define a provider-independent interface for image generation, editing and
  variation. Provide an OpenAI API adapter and an OpenAI-compatible self-hosted
  adapter.
- Let the administrator configure default provider, model, base URL and
  credentials through backend environment variables. Do not expose provider,
  model or image parameter selection to end users.
- Return clear unsupported-operation errors. Never report provider or storage
  failures as successful image creation.
- Keep credentials out of the database, API responses and logs.
- Use deterministic fake providers for automated tests. Run live provider
  checks separately when credentials and a compatible endpoint are available.
- Implement a user-requested variation through the provider's supported edit
  contract. Do not call the deprecated legacy `/images/variations` endpoint.

## Alternatives considered

- Keep only session memory: rejected because users must reopen prompts/images
  after logout and later sessions.
- Store image bytes in SQLite: rejected because file content belongs on a local
  volume while structured metadata belongs in the database.
- Let users choose provider/model/size: rejected because the user asked for one
  admin-configured default and a simple interface.
- Add a job queue or object storage now: deferred until throughput or
  multi-host durability needs justify added infrastructure.

## Consequences

- SQLite plus a local volume keeps the MVP deployable on one machine and keeps
  records durable across application restarts.
- Local storage requires explicit backup and does not coordinate multiple
  application hosts.
- Image API capability differences remain inside adapters. A provider without
  a requested operation must return a clear error.
- Synchronous provider requests can hold an HTTP request open; a queue can be
  added later if real usage requires it.
- Password and cookie handling become part of the product security boundary.

## Review triggers

- The app needs multi-host deployment, stronger backup guarantees or object
  storage.
- Provider API contract changes or an adapter cannot support required actions.
- The product adds sharing, user-selected model settings, payment, quota or
  manual image tools.

## References

- [OpenAI image generation and editing guide](https://developers.openai.com/api/docs/guides/image-generation)
- [OpenAI Images API reference](https://developers.openai.com/api/reference/resources/images)
