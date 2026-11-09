# ADR 0008 — Vietnamese prompt interpretation

Date: 2026-11-09
Status: Accepted
Extends: ADR 0005 and ADR 0006

## Context

The Vietnamese UI accepted Unicode prompts, but sent them unchanged to the
image-generation provider. Image providers may interpret non-English
descriptions inconsistently. The product should understand Vietnamese while
keeping the user's original description in the private image history.

## Decision

- Add a server-side, OpenAI-compatible chat-model step before image generation,
  editing and variation. It interprets Vietnamese and other languages, then
  returns a concise English image instruction.
- Select the language model, endpoint and credential through `PROMPT_MODEL`,
  `PROMPT_API_BASE_URL` and `PROMPT_API_KEY`; reuse `OPENAI_API_KEY` only when
  the prompt endpoint matches `OPENAI_BASE_URL`. Default to `gpt-6-luna`. Do not
  expose model configuration in the UI or API.
- Save and display the original prompt. Send only the interpreted instruction
  to the image provider. Preserve exact text the user asks to render in its
  original language.
- If prompt interpretation fails, mark the operation failed with a safe error.
  Do not silently send the unprocessed prompt to the image provider.
- Keep prompt text out of LangSmith traces.

## Alternatives considered

- Send Vietnamese directly to the image provider: rejected because the product
  should reliably interpret the user's language independently of the selected
  image model.
- Store the rewritten prompt as the only history: rejected because users need
  to see the words they actually entered.
- Let users select the language or model: rejected because provider/model
  configuration stays server-side.

## Consequences

- Each image operation adds a chat-model request, latency and cost.
- The user's prompt is sent to both the language-model endpoint and image
  provider. Deployment requires language-model credentials or a reachable
  compatible endpoint.
- A language-model failure prevents image generation, editing or variation.
- Live Vietnamese prompt checks remain separate from offline application
  checks and require valid credentials and endpoints.

## Review triggers

- The image provider documents reliable Vietnamese handling for every supported
  operation and a separate language-model request is no longer needed.
- Prompt interpretation needs streaming, user-visible revisions or per-user
  controls.

## References

- [GPT-6 Luna model](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [OpenAI models and multilingual capabilities](https://developers.openai.com/api/docs/models)
- [OpenAI Chat Completions API](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
- [OpenAI image generation guide](https://developers.openai.com/api/docs/guides/image-generation)
