---
name: relay-imagegen
description: Generate or edit images through RC (Right Code, the AI image-generation API service at rightapi.ai). Use when the user says RC, Right Code, rightapi.ai, right.codes, or relay-imagegen, or an active image router selects RC. Also configure or check RC authentication. Do not override an explicit choice of the host's built-in image tool or another provider.
---

# relay-imagegen

**RC (Right Code)** is an image-generation relay: the AI image-generation API service at [rightapi.ai](https://www.rightapi.ai), relaying models such as `gpt-image` and `nano-banana`. This skill generates and edits images through RC; **RC** is the shorthand used throughout.

Use the bundled `scripts/generate_image.py` with Python 3. RC is the default; leave the Codex `config.toml` unchanged. Resolve scripts relative to this skill, regardless of the current project directory.

## 1. Generate or edit

```bash
python3 scripts/generate_image.py --prompt "一只戴着太空头盔的橘猫" --filename orange-cat-astronaut
```

Default: RC, `gpt-image-2.5-flare`, `--size 16:9` (translated to `1536x864`), provider quality `auto`.

Model names follow the [RC image API documentation](https://docs.rightapi.ai/docs/rc_draw/) (checked 2026-10-15):

| Model | Use |
|---|---|
| `gpt-image-2.5-flare` | Default; daily generation, speed priority |
| `gpt-image-2.5-sunburst` | Prefer for precise editing, multi-image composition and text/detail work |
| `gpt-image-2` | Base model; quality up to `high` |
| `gemini-3-pro-image-preview` | Nano Banana Pro; Gemini generation and reference editing |
| `gemini-nano-banana-2.1` | Nano Banana 2 series; speed priority |

Do not use the old `gpt-image-2.5`, `gpt-image-2-vip` or `nano-banana-*` API names for new submissions. Keep explicit model choices; when the user names an obsolete model, explain the current choices rather than silently substituting one.

Reference prices from the 2026-09 list (top-up 1$ = ¥1.00; the RC console is authoritative): `gpt-image-2` $0.04/image, `gpt-image-2.5-flare` $0.06, `gpt-image-2.5-sunburst` TBC, `gemini-nano-banana-2.1` $0.12, `gemini-3-pro-image-preview` $0.18. README section 6 maps these onto the old model names.

- GPT Image uses pixel `--size`, such as `2048x1152` or `3840x2160`. Width/height must be multiples of 16, at most 3840 each, aspect ratio at most 3:1, and total pixels 655,360–8,294,400. Sizes above 2560x1440 are experimental per RC.
- Existing ratio syntax remains convenient: `--size 16:9 --image-size 2K` translates locally to `2048x1152`; `4K` translates to `3840x2160`. Other ratios are capped to the pixel limits. Omit `--image-size` with an explicit pixel size; it is not a GPT API field.
- GPT `--quality` accepts `auto`, `low`, `medium`, `high`; the two 2.5 models also accept `xhigh` and `max`. Use higher quality when requested or needed, not automatically for every image.
- GPT also supports `--output-format png|jpeg|webp`, `--output-compression 0..100` (jpeg/webp only), and `--moderation auto|low`.
- Gemini uses aspect-ratio `--size` plus `--image-size 1K|2K|4K` (default `1K`). A tier unsupported by the chosen model may be rejected. GPT-only quality/format options do not apply.
- Transparent backgrounds, mask-based inpainting and variations are not currently supported by RC. Describe local edits in the prompt; do not promise an alpha cutout.

- Edit through RC by adding one `--reference /absolute/path/image.png` per reference.
- Use `--count N` for N sequential single-image tasks. Provider field `n` stays 1.
- **Always provide `--filename` with a descriptive English name** (without extension). 
  - For non-English prompts, automatically generate a short, descriptive English filename based on the prompt content
  - Examples: `--filename "orange-cat-astronaut"`, `--filename "running-dog"`, `--filename "sunset-mountain"`
  - Keep it simple: 2-4 words describing the main subject and action/scene
  - Use lowercase with hyphens, no special characters
  - If the user provides a filename, use it as-is; otherwise generate one from the prompt
- Use `--help` when other arguments are needed.

A request to generate or edit authorizes the requested images. State the selected provider and count briefly, then proceed.

**Primary provider:** RC is the default and preferred provider.

RC is the only provider in this Skill.

## 2. Keys

Read keys internally; never print them or request them in chat.

| Provider | Environment variable | Key file |
|---|---|---|
| RC (Right Code) | `RIGHT_CODES_API_KEY` | `~/.config/right-code/api_key` |

For RC setup, run `python3 scripts/configure_api_key.py`, then `--check`; report status and saved path only. It uses hidden local input. If needed, link to [registration](https://www.rightapi.ai/register?aff=9ec111f0) and [key creation](https://docs.rightapi.ai/docs/rc_quick_start/apikey.html). Local configuration checks do not prove live generation access. Do not generate a paid image solely to check a key unless the user requested a live test.

## 3. Recovery

```bash
python3 scripts/generate_image.py --resume-task-id TASK_ID
```

Use the original output root when resuming, including the same explicit `--output-dir` if supplied.

- RC resumes remote polling without resubmitting. The client retries transient polling errors with bounded backoff.
- Every failure prints one JSON object: `{"status": "error", "kind": ..., "message": ..., "checkpoint": ...}`. Exit code `2` means stop; exit code `3` means retryable — wait, then resume with `--resume-task-id TASK_ID`.
- Stop kinds (exit `2`): `auth_error` (fix the key first), `submission_ambiguous` (submit outcome unknown — never resubmit blindly; check the RC console for a charged task before any new submission), `task_failed`, `unknown_status`, `bad_response`, `http_error`, `error`.
- Retryable kinds (exit `3`): `transient_poll`, `poll_timeout`.
- If no task can be recovered, allow at most three total submissions per intended image under the original request; stop for authentication failures, unexpected cost or an uncertain submission outcome.
- Never combine resume with a new prompt, references or multiple outputs.

## 4. Output

Outputs use the project-local layout when a project root exists, otherwise the personal pictures library:

```text
<project>/output/images/          (inside a project)
~/Pictures/AI-generates-images/   (no project root)
  YYYY-MM-DD/YYMMDD-HHMM-NNN-content.png
  .prompts/YYYY-MM-DD/YYMMDD-HHMM-NNN-content.md
  .tasks/rightcode/...
```

The nearest Git/Mercurial root takes precedence over package markers. Pass `--output-dir` to place images anywhere explicitly; never fall back to Downloads, Desktop or agent internal state. An explicit directory keeps hidden `.prompts` and `.tasks` sidecars. Existing artifacts are not deleted. RC still finds legacy `generated_images/.tasks/rightcode` checkpoints.

Prompt records contain the provider, model, size, quality (when supplied), operation, timestamp and full prompt, without secrets or temporary URLs. Task records may contain temporary image URLs for recovery. Generated artifacts are ignored by the managed output root's `.gitignore`.

Read final JSON. Display saved originals and link each image and matching prompt file. Report partial failures accurately; a model listing or quote is not a successful generation. Confirm image format and actual dimensions before reporting a live test as successful.

## 5. RC protocol

Use `https://www.rightapi.ai` with protocol-specific requests:

- GPT generation: `POST /v1/images/generations`; editing: `POST /v1/images/edits`, with JSON `image` data URLs for local references. Keep `async: true` and `n: 1`.
- Gemini generation and editing: `POST /v1beta/models/{model}:generateContent`; prompt and reference `inline_data` parts go in `contents`, and ratio/tier in `generationConfig.imageConfig`. Keep `async: true`; generate one image per task (no GPT `n` field).
- Poll both at `GET /v1/tasks/{task_id}`. Preserve immediate checkpoints. Completed results may omit status: GPT uses `data[].url`, Gemini uses `candidates[].content.parts[].text` URLs. `failed`, `expired` and `canceled` are terminal failures.

RC currently returns URLs, not base64 (`response_format` has no effect). Keep legacy base64/inline response parsing for resumable older tasks. Download original bytes before presenting results.
