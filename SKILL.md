---
name: relay-imagegen
description: Generate raster images through Codex666 AI's Media API, then save and display provider originals. Use only when the user explicitly requests relay-imagegen or Codex666 AI. The default is gpt-image-2 at 1K; use another named Media API image model for 2K or 4K. Do not use for video, Right Code's asynchronous draw API, DuckCoding, Gemini-native calls, or the host agent's built-in image generator.
---

# Relay Image Generator

Use `scripts/generate_image.py` for Codex666 AI Media API image generation. Keep its credentials, API route, and output directory separate.

## Provider routes

| Service route | Key | Default |
|---|---|---|
| `https://codex666ai.com:8443/media/v1` | `CODEX666AI_API_KEY` or `~/.config/codex666ai/api_key` | `gpt-image-2`, `1K`, `medium` |

This skill always calls Codex666 AI Media API. It reads the live model directory and requests a quote before each image task. Do not change its API route or switch services; each additional paid attempt requires explicit authorization.

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
python3 "$SCRIPT" --provider codex666ai --list-models
```

Generate through an OpenAI-compatible route:

```bash
python3 "$SCRIPT" --model nano-banana-pro --size 2K \
  --prompt 'A cinematic orange cat astronaut in deep space'
```

Show a no-charge quote before a paid request:

```bash
python3 "$SCRIPT" --model firefly-gpt-image-2 --size 4K \
  --prompt 'A cinematic orange cat astronaut in deep space' --quote
```

Video models are intentionally excluded from this skill.

## Verification rules

Treat the downloaded artifact as the result of record. After generation:

1. Measure dimensions with `sips -g pixelWidth -g pixelHeight <file>`.
2. Check the actual format from file bytes rather than the requested extension.
3. Preserve the original and display every result with an absolute Markdown image path.
4. Report provider route, operation, model, requested size, actual pixels, quality when present, returned count, and the matching prompt-file paths.

## Verified behavior

The current Media API model directory and quotes were rechecked on 2026-08-31. A `gpt-image-2` 1K request completed; requests to other models later received upstream HTTP 502 responses, so treat their live generation availability as unverified until the provider resolves that outage.

| Behavior | `codex666ai` |
|---|---|
| Generation | verified |
| `gpt-image-2` 1K generation | verified, 1254x1254 PNG |
| Other image models / 2K / 4K generation | model directory and quote verified; live generation pending provider 502 recovery |

## Response handling

Accept `data[].url` and `data[].b64_json`. Download remote output before display. Send the bearer key only to the selected provider's own hosts.

Return the operation stage, HTTP status, quote, and provider message on errors. Keep already-saved files.
