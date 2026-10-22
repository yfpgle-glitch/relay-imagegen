<div align="center">

# relay-imagegen

**Generate and edit images through RC in Codex, Claude Code, and WorkBuddy**

**RC (Right Code)** is a relay — the AI image-generation API service at [rightapi.ai](https://www.rightapi.ai), relaying models such as `gpt-image` and `nano-banana`. Images start at **$0.04 each** (default model $0.06, top-up at 1$ = ¥1.00); the RC console is authoritative. Just say **RC**.

![Agents](https://img.shields.io/badge/agents-Codex%20%7C%20Claude%20Code%20%7C%20WorkBuddy-202124?style=flat-square)
![Provider](https://img.shields.io/badge/provider-RC%20%28Right%20Code%29-2563EB?style=flat-square)
![Model](https://img.shields.io/badge/model-gpt--image--2.5--flare-16A34A?style=flat-square)

[GitHub repository](https://github.com/yfpgle-glitch/relay-imagegen) · [中文](README.md) · English

</div>

---

## 1. Install the Skill

Python 3 is required. If it is missing, ask Codex, Claude Code, or WorkBuddy to install it.

### 1) Codex / Claude Code

Send this message to Codex or Claude Code:

```text
Install the root of this repository as a Skill:
https://github.com/yfpgle-glitch/relay-imagegen
```

After installation, open a new task or session if the Skill is not detected.

### 2) WorkBuddy

1. [Download the Skill archive](https://github.com/yfpgle-glitch/relay-imagegen/archive/refs/heads/main.zip).
2. In WorkBuddy, open **Add Skill** and select **Upload Skill**.
3. Upload the archive you downloaded.

## 2. Create an API key

1. [Register with RC (Right Code)](https://www.rightapi.ai/register?aff=9ec111f0) and sign in. (Register through this link to receive 5% extra credit on every top-up.)
2. Open **Token Management**.
3. Select **Create Key**.

For more help, read the [official RC API key guide](https://docs.rightapi.ai/docs/rc_quick_start/apikey.html).

## 3. Configure the API key

After installation, tell Codex, Claude Code, or WorkBuddy:

```text
Configure my RC API key.
```

The tool will open a hidden input box. Paste the API key and confirm. The key is hidden while you type.

## 4. Use the Skill

Tell the current tool what you want:

- `Use RC to generate a cinematic 16:9 image.`
- `Use RC to edit this image.`
- `Use RC to generate three different versions.`
- `Resume the RC task task_example.`

The defaults are `gpt-image-2.5-flare` and `16:9` (translated to `1536x864`), with provider quality `auto`. Prefer `gpt-image-2.5-sunburst` for precise edits, multi-image composition and text/detail work.

GPT models accept explicit pixels, for example `--size 2048x1152 --quality xhigh`; `xhigh` / `max` require a 2.5 model. Existing ratio syntax still works: `--size 16:9 --image-size 2K` becomes `2048x1152`, and `4K` becomes `3840x2160`. Omit `--image-size` with explicit pixels. RC treats sizes above `2560x1440` as experimental.

For Gemini, choose `--model gemini-3-pro-image-preview` or `gemini-nano-banana-2.1` and set ratio/tier with `--size 16:9 --image-size 2K`. Use `--reference /absolute/path/image.png` for references; the script selects the appropriate editing protocol.

RC currently does not support transparent backgrounds, mask inpainting or variations. Describe local edits in the prompt.

Each image is submitted separately. Generating several images may result in several charges.

## 5. Where images are saved

Generated images are archived by date automatically:

- Inside a project: `<project>/output/images/YYYY-MM-DD/`
- Outside any project: `~/Pictures/AI-generates-images/YYYY-MM-DD/` (visible in the macOS Finder and Windows File Explorer pictures folders)

Filenames look like `260917-1645-001-space-helmet-cat-cycling.png` (timestamp-sequence-content), with a matching `.md` recording the model, size and full prompt. You can also pass an explicit output directory.

## 6. Models & pricing

Images are billed per generation; credit is topped up at 1$ = ¥1.00. Prices below come from the 2026-09 list and are kept as a reference — they may change after model revisions, so **the RC console is authoritative**:

| Model | Price | Use |
|---|---:|---|
| `gpt-image-2` | $0.04/image | Base model, fixed size, quality up to `high`, lowest price |
| `gpt-image-2.5-flare` | $0.06/image | **Default**; daily generation, speed priority |
| `gpt-image-2.5-sunburst` | TBC | Precise edits, multi-image composition, text and detail; no counterpart in the 2026-09 list |
| `gemini-nano-banana-2.1` | $0.12/image | Nano Banana 2 series; speed priority (was `nano-banana-2`) |
| `gemini-3-pro-image-preview` | $0.18/image | Nano Banana Pro; quality and understanding priority (was `nano-banana-pro`) |

Where the prices come from:

- Reference prices are taken from the 2026-09-17 list. Old names mapped as: `gpt-image-2` $0.04, `gpt-image-2.5` $0.06 (default), `nano-banana-2` $0.12, `gpt-image-2-vip` $0.13, `nano-banana-pro` $0.18, `nano-banana-2-lite` $0.05.
- `gpt-image-2.5-flare` inherits the old default `gpt-image-2.5` price; `gpt-image-2.5-sunburst` is a higher-quality tier added in the same revision with no counterpart in the old list — confirm it in the RC console.
- Old `gpt-image-2-vip` ($0.13, 2K/4K) and `nano-banana-2-lite` ($0.05) have no direct successor in the current list; pick from what the console offers when you need 2K/4K.
- For daily generation the default `gpt-image-2.5-flare` is enough.

Old model names and fixed-dimension measurements are no longer the basis for current requests. See the RC console for account availability and current task pricing, and the [official image API documentation](https://docs.rightapi.ai/docs/rc_draw/) for current protocols and parameters.
