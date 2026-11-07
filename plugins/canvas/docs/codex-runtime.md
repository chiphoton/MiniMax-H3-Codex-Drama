# Codex runtime verification

Verified November 8, 2026 for Canvas 0.6.0.

## SDK and CLI

`@openai/codex-sdk` and its bundled `@openai/codex` CLI are pinned to **0.167.0**, the npm `latest` releases checked on this date. The previous pins were 0.152.1. Other existing dependency versions are unchanged.

Canvas prefers the installed app/CLI on PATH over npm's bundled CLI, preserving the user's signed-in environment and native tools. `CANVAS_CODEX_PATH` overrides that choice. The installed app CLI used for the live generation was **0.167.0-alpha.3.2**; the application bundle was not modified. The stable bundled CLI reports **0.167.0**.

The existing SDK wrapper remains compatible. `npm run check` passed the browser builds, TypeScript checks, and **574 tests**, including SDK process launching, scoped MCP tools, model discovery, image imports, and startup-error handling.

A subsequent [live sidebar workflow test](sidebar-image-e2e.md) verified chained native generation and editing, found and fixed scoped MCP approval, image-mode discovery, and resumed-turn transcript issues, and passed **576 tests**.

## General models

Both CLI versions were queried through their app-server protocol. The live catalog selected `gpt-6.1-sol` as default and returned:

- `gpt-6.1-sol`
- `gpt-6-astra`
- `gpt-6.1-terra`
- `gpt-6-sol`
- `gpt-6-luna`
- `gpt-5.6-sol`
- `gpt-5.6-terra`
- `gpt-5.6-luna`

These are verification results, not built-in choices. Canvas continues to use the runtime's catalog, default effort, and modality information. Saved explicit selections remain unchanged. This follows the [official model-list guidance](https://learn.chatgpt.com/docs/app-server#list-models-modellist).

## Native image generation

The app-server `modelProvider/capabilities/read` response reported `imageGeneration: true`, and the CLI feature listing reported native image generation enabled. The model picker selects the agent that invokes image generation; it does not select an image backend.

A real `CodexPlanImageRuntime` call through SDK 0.167.0 and the preferred app CLI used the live default `gpt-6.1-sol`, its default low effort, and Standard service. It invoked the native image tool exactly once and successfully imported a 1,910,860-byte PNG from that SDK thread's generated-images directory. The image was inspected and matched the synthetic teapot prompt. No user project or Canvas data directory was used.

Verification image SHA-256: `30418b0ae2f9376677daa04d738b43cfde81f198ccf32f4b37f7cb5ddda82946`.

Prompt: “A studio photograph of a small glossy teal ceramic teapot on a plain cream background, soft shadow, no text.” The requested canvas was 1024 × 1024; dimensions are instructions to the native tool rather than an enforced output transform.

The [official Codex image-generation page](https://learn.chatgpt.com/codex/image-generation) describes the built-in backend as **GPT Image 2**. The current [API image-generation guide](https://developers.openai.com/api/docs/guides/image-generation#gpt-image-26) separately documents **GPT Image 2.6 Sunburst and Flare**. Neither the native tool's parameters nor this result exposes an independently selectable or returned backend model version. This check verifies working native plan generation; it does not establish GPT Image 2.6 access through the plan. No API-key fallback was used.

Restart Canvas after rebuilding to load the updated SDK. Refresh **Settings → Connections → Codex Plan** to reload the account's general-model catalog. Image generation stays on the native plan route.
