---
name: relay-imagegen
description: Generate or edit images through RC (Right Code, the AI image-generation API service at rightapi.ai). Use when the user says RC, Right Code, rightapi.ai, right.codes, or relay-imagegen, or an active image router selects RC. Also configure or check RC authentication. Do not override an explicit choice of the host's built-in image tool or another provider.
---

# relay-imagegen

**RC (Right Code)** is an image-generation relay: the AI image-generation API service at [rightapi.ai](https://www.rightapi.ai), relaying models such as `gpt-image` and `nano-banana`. This skill generates and edits images through RC; **RC** is the shorthand used throughout.

Use the bundled `scripts/generate_image.py` with Python 3. RC is the default; leave the Codex `config.toml` unchanged. Resolve scripts relative to this skill, regardless of the current project directory.

## 1. Generate or edit

```bash
python3 scripts/generate_image.py --prompt "一只戴着太空头盔的橘猫"
```

Default: RC, `gpt-image-2.5`, `--size 16:9`, `--image-size 1K`.

`--image-size` is model-dependent: `gpt-image-2-vip` honors 2K/4K (measured 2048x1152 / 3840x2160 at 16:9) and so does `nano-banana-pro`; `gpt-image-2.5` and `gpt-image-2` ignore the tier and render one fixed size per aspect ratio (1672x940 at 16:9). Use `--model gpt-image-2-vip` or `nano-banana-pro` when the user asks for 2K/4K.

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

Prompt records contain the provider, model, size, operation, timestamp and full prompt, without secrets or temporary URLs. Task records may contain temporary image URLs for recovery. Generated artifacts are ignored by the managed output root's `.gitignore`.

Read final JSON. Display saved originals and link each image and matching prompt file. Report partial failures accurately; a model listing or quote is not a successful generation. Confirm image format and actual dimensions before reporting a live test as successful.

## 5. RC protocol

Keep asynchronous submission to `https://www.rightapi.ai/draw/v1/images/generations` and polling at `https://www.rightapi.ai/v1/tasks/{task_id}`. Preserve `async: true`, `n: 1`, immediate checkpoints, and completed responses containing URL/base64/inline images even without a status. Download original bytes before presenting results.
