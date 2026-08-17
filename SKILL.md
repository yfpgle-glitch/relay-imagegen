---
name: relay-imagegen
description: Generate and edit raster images across user-configured third-party relays that expose OpenAI-compatible Images APIs (/v1/images/generations and /v1/images/edits), save results locally, and display them. Use only when the user explicitly requests relay-imagegen, 1pkapi or 皓悦API, CallAI, Codex666 AI, another configured relay, a custom compatible base URL, or a hard capability that the current rightcode-image skill does not document but a configured relay does, such as mask editing or true 8K output. Do not select this skill merely because a request mentions image generation, reference editing, or a generic model such as gpt-image-2; when a third-party provider is requested but not named, default to rightcode-image. Do not use for Right Code's asynchronous draw API, DuckCoding, Gemini-native calls, or the host agent's built-in image generator.
---

# Relay Image Generator

Use the bundled client for synchronous generation and synchronous multipart editing against any OpenAI-compatible Images endpoint. Each provider keeps its own key, base URL, and output directory; never mix them.

This is a specialized relay executor, not the default third-party image generator. Its internal provider preference applies only after this skill has been selected by the user or by a verified relay-only capability requirement.

## Providers

| Slug | Label | Base URL | Key env var | Key file | Default size/quality | Cost per image |
|------|-------|----------|-------------|----------|----------------------|----------------|
| `1pkapi` (default) | 皓悦API | `https://1pkapi.com` | `ONEPK_API_KEY` | `~/.config/1pkapi/api_key` | `4096x4096` / `high` | 0.05 flat, any size |
| `callai` | CallAI | `https://sub.callai.one` | `CALLAI_API_KEY` | `~/.config/callai/api_key` | `4096x4096` / `high` | 0.08 at 2K, 0.1 at 4K |
| `codex666ai` | Codex666 AI | `https://api.codex666ai.com` | `CODEX666AI_API_KEY` | `~/.config/codex666ai/api_key` | `1536x1024` / `high` | 0.06, capped at 1254px |

Prefer `1pkapi`: it is the cheapest and its flat rate makes max settings free. Fall back to `callai` when `1pkapi` is out of credit or its single `gpt-image-2` model is not enough. Reach for `codex666ai` only when something specifically needs it — it costs more than `1pkapi` and cannot deliver 4K.

Select one with `--provider <slug>`. The env var wins over the key file. When `--output-dir` is omitted, detect the nearest project root and save previews under `<project>/.generated_images/third-party/relay/<slug>`. With no detected project, use `~/Downloads/generated_images/third-party/relay/<slug>` on macOS and `~/Desktop/generated_images/third-party/relay/<slug>` on Windows. Filenames are also prefixed with the slug, so providers never collide. Never create an `outputs/` directory by default; an explicit `--output-dir` always wins.

`https://codex666ai.com/` is the website, not an API base. Adding a provider means adding an entry to `PROVIDERS` in the script; use `--base-url` only for a one-off probe.

## Endpoints

- `GET /v1/models` — preflight, free
- `POST /v1/images/generations` — text to image, paid
- `POST /v1/images/edits` — multipart reference/mask editing, paid

## Defaults

- Model: `gpt-image-2`
- Size: `1536x1024`
- Quality: `high`
- Count: `1`
- Format: `png`

## Workflow

1. Treat generation and editing as paid. If the user has not clearly requested a live operation, explain the planned request and wait for confirmation.
2. Read the key from the provider's env var, then its key file. Never ask for a key in chat or print it.
3. Query `GET /v1/models` before a new paid request. The client rejects unavailable model names before submission.
4. Use synchronous mode only. Do not send requests to async endpoints.
5. Preserve provider originals locally. Keep preview-only work in the detected default directory. Use an explicit existing project asset directory only for a selected project-bound final asset or a user-named destination. `--aspect-ratio` creates centered cropped copies and keeps originals.
6. Display every saved result using an absolute Markdown image path and clickable file link. Report provider, operation, model, size, quality, and count.

## Script location

Resolve `scripts/generate_image.py` against this skill's own directory. The installed path differs per host agent, so never copy one agent's absolute path into the other:

- Codex: `~/.codex/skills/relay-imagegen/scripts/generate_image.py`
- Claude Code: `~/.claude/skills/relay-imagegen/scripts/generate_image.py`

The commands below use `$SCRIPT`. Set it once before the first call, using the path for the current agent:

```bash
SCRIPT=~/.claude/skills/relay-imagegen/scripts/generate_image.py
```

## Commands

Show configured providers and whether each key is present, without any network call:

```bash
python3 "$SCRIPT" --list-providers
```

List models on one provider:

```bash
python3 "$SCRIPT" --provider callai --list-models
```

Generate synchronously:

```bash
python3 "$SCRIPT" --provider callai \
  --prompt 'A cinematic orange cat astronaut in deep space'
```

Edit one or more reference images with multipart upload:

```bash
python3 "$SCRIPT" --provider callai \
  --prompt 'Change the orange suit accents to bright blue' \
  --image /absolute/path/source.png
```

Append `--mask /absolute/path/mask.png` for masked editing. Repeat `--image` for multiple references. Both are live-tested on all three providers.

`--output-compression`, `--background`, `--moderation`, `--response-format`, and `--user` are forwarded to the relay, but see the capability matrix below: `--background` and `--output-format` are currently ignored by every configured provider.

## Current verified behavior

Recheck `/v1/models` per provider because account groups change.

Relays silently ignore parameters they do not support: they accept the request, return `completed`, and deliver something smaller or plainer than asked. Verify the artifact, not the status. Measure pixels with `sips -g pixelWidth -g pixelHeight`, check the format with `head -c 4 file | xxd -p` (PNG is `89504e47`), and check transparency with `sips -g hasAlpha`.

### Capability matrix, all live-tested 2026-08-13

| Capability | `1pkapi` | `callai` | `codex666ai` |
|---|---|---|---|
| Generation | yes | yes | yes |
| Reference-image edit | yes | yes | yes |
| Mask edit | yes | yes | yes |
| Multiple `--image` | yes | yes | yes |
| `--count 2` | 2 returned | 2 returned | 1 returned |
| True 4K | yes | yes | no, capped at 1254px |
| `--background transparent` | ignored | ignored | ignored |
| `--output-format webp` | ignored, PNG | ignored, PNG | ignored, PNG |

`--background` and `--output-format` are accepted by the CLI and forwarded, but no configured relay honors them today. Do not promise transparency or WebP; crop or convert locally instead. `--aspect-ratio` is local `sips` cropping and is exact: a 4096x4096 original yields 4096x2304 at `16:9` and 2304x4096 at `9:16`.

`1pkapi` (皓悦API):

- `/v1/models` returns only `gpt-image-2`.
- Delivers true 4096x4096, 8192x8192, and 16384x16384, pixel-verified.
- Flat rate per call: `usage.outputTokens` was 6500 at `1024x1024`, `4096x4096`, and `8192x8192` alike, so max settings cost nothing extra. Defaults to `4096x4096` / `high`.
- Returns `INSUFFICIENT_BALANCE` once credit runs out, on every size including small ones. Treat that as a billing state, not a size limit.

`callai`:

- `/v1/models` lists 13 models, but only `gpt-image-2` actually generates. `gpt-image-1` and `gpt-image-1.5` returned Cloudflare `502` on three consecutive attempts each; a listed model is not a usable model.
- Delivers true 4096x4096 and 8192x8192, pixel-verified.
- Billed in tiers by size, confirmed against the account's own billing: 2K costs 0.08, 4K costs 0.1. Reported `usage.output_tokens` also scales with size (16896 at 4096, 67584 at 8192). Defaults to `4096x4096` / `high` because 4K costs 25% more for 4x the pixels, but size is not free here — pass a smaller `--size` when 4K is not needed.
- Transient `SSL: UNEXPECTED_EOF_WHILE_READING` and Cloudflare `502` both appear under load. Retry once before reporting an outage.

`codex666ai`:

- `/v1/models` returned only `gpt-image-2` on 2026-08-13.
- Does not honor large sizes. A `4096x4096` request returns `completed` but delivers 1254x1254, over both `url` and `b64_json`. Keep it at `1536x1024`.
- Silently caps batches: `--count 2` returns a single image.
- Async image tasks return `404: async image tasks are not enabled` and are intentionally not implemented.
- Gemini batch discovery returns `404: batch image API is disabled`.
- Image access is per key group. A key can authenticate and list text models yet still fail generation with `Image generation is not enabled for this group`.

## Response and failure handling

Accept `data[].url` and `data[].b64_json`. Download remote output before display. Send the bearer key only to the selected provider's own hosts, never unrelated CDNs.

Return the operation stage, HTTP status, and provider message. Distinguish model preflight, generation, edit, and download failures. Keep already-saved files.

Do not claim Gemini-native generation, batch generation, streaming previews, or partial-image handling until each path is implemented and live-tested.
