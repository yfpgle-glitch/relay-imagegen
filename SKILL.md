---
name: relay-imagegen
description: Generate and edit raster images through user-configured third-party relays that expose OpenAI-compatible Images APIs, then save and display provider originals. Use only when the user explicitly requests relay-imagegen, 1pkapi or 皓悦API, CallAI, Codex666 AI, another configured relay, a custom compatible base URL, or a verified relay-only capability such as mask editing. A generic third-party image request without a named provider defaults to rightcode-image. Do not use for Right Code's asynchronous draw API, DuckCoding, Gemini-native calls, or the host agent's built-in image generator.
---

# Relay Image Generator

Use `scripts/generate_image.py` for named third-party relays. Keep each service's credentials, API route, and output directory separate.

## Provider routes

| Slug | Service route | Key | Default |
|---|---|---|---|
| `1pkapi` | `https://1pkapi.com/v1/images/*` | `ONEPK_API_KEY` or `~/.config/1pkapi/api_key` | `gpt-image-2`, `4096x4096`, `high` |
| `callai` | `https://sub.callai.one/v1/images/*` | `CALLAI_API_KEY` or `~/.config/callai/api_key` | `gpt-image-2`, `4096x4096`, `high` |
| `codex666ai` | `https://api.codex666ai.com/v1/images/*` | `CODEX666AI_API_KEY` or `~/.config/codex666ai/api_key` | `gpt-image-2`, `1536x1024`, `high` |

Use the route named by the user. Within this skill, `1pkapi` is the default only when no relay slug was named. Keep the selected route after a failure; switching services or adding paid attempts requires explicit authorization.

Use `codex666ai` only when the user explicitly names Codex666 AI.

## Cost and authorization

Treat generation and editing as paid. Proceed only when the user clearly requested a live operation. Model listing is a free preflight.

Read keys from the provider environment variable first, then its key file. Never ask for a key in chat or print it.

## Output location

When `--output-dir` is omitted, both image skills use the same project-local structure:

```text
<project>/generated_images/
  images/YYYY-MM-DD/YYYYMMDD-HHMMSS-NNN-content.png
  prompts/YYYY-MM-DD/YYYYMMDD-HHMMSS-NNN-content.md
  .tasks/relay/
```

The image name sorts chronologically, and each image has a same-stem Markdown prompt record containing provider, model, requested size/quality, operation, timestamp, and full prompt. `generated_images/.gitignore` ignores generated artifacts. If no project root is detected, stop and request an explicit `--output-dir`; do not use Downloads, Desktop, or Codex internal directories. An explicit `--output-dir` wins and stores sidecars in hidden `.prompts` and `.tasks` directories. `--aspect-ratio` creates a centered local crop while preserving the provider original and writes a matching prompt record for the crop.

## Script location

Resolve the script relative to this Skill:

- Codex: `~/.codex/skills/relay-imagegen/scripts/generate_image.py`
- Claude Code: `~/.claude/skills/relay-imagegen/scripts/generate_image.py`

Set `$SCRIPT` to the active host path before using the examples.

## Commands

Show local provider configuration without a network call:

```bash
python3 "$SCRIPT" --list-providers
```

List models on one provider:

```bash
python3 "$SCRIPT" --provider callai --list-models
```

Generate through an OpenAI-compatible route:

```bash
python3 "$SCRIPT" --provider callai \
  --prompt 'A cinematic orange cat astronaut in deep space'
```

Edit one or more references through a verified editing route:

```bash
python3 "$SCRIPT" --provider callai \
  --prompt 'Change the orange suit accents to bright blue' \
  --image /absolute/path/source.png
```

Append `--mask /absolute/path/mask.png` for masked editing. Repeat `--image` for multiple references.

## Verification rules

Treat the downloaded artifact as the result of record. After generation:

1. Measure dimensions with `sips -g pixelWidth -g pixelHeight <file>`.
2. Check the actual format from file bytes rather than the requested extension.
3. Preserve the original and display every result with an absolute Markdown image path.
4. Report provider route, operation, model, requested size, actual pixels, quality when present, returned count, and the matching prompt-file paths.

## Verified behavior

The OpenAI-compatible routes were live-tested on 2026-08-13. Codex666 size behavior was rechecked on 2026-08-17.

| Behavior | `1pkapi` | `callai` | `codex666ai` |
|---|---|---|---|
| Generation | verified | verified | verified |
| Reference edit | verified | verified | verified |
| Mask edit | verified | verified | verified |
| Multiple references | verified | verified | verified |
| Two-image request | two files | two files | one file |
| High-resolution artifact | 4096px and above verified | 4096px and above verified | 1254x1254 from both 2048x2048 and 4096x4096 requests |
| Transparent background request | PNG with the provider-rendered background | PNG with the provider-rendered background | PNG with the provider-rendered background |
| WebP request | PNG artifact | PNG artifact | PNG artifact |

## Response handling

Accept `data[].url` and `data[].b64_json`. Download remote output before display. Send the bearer key only to the selected provider's own hosts.

Return the operation stage, HTTP status, and provider message on errors. Keep already-saved files.
