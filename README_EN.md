<div align="center">

# relay-imagegen

**Generate and edit images through RC in Codex, Claude Code, and WorkBuddy**

**RC (Right Code)** is a relay — the AI image-generation API service at [rightapi.ai](https://www.rightapi.ai), relaying models such as `gpt-image` and `nano-banana`. Just say **RC**.

![Agents](https://img.shields.io/badge/agents-Codex%20%7C%20Claude%20Code%20%7C%20WorkBuddy-202124?style=flat-square)
![Provider](https://img.shields.io/badge/provider-RC%20%28Right%20Code%29-2563EB?style=flat-square)
![Model](https://img.shields.io/badge/model-gpt--image--2.5-16A34A?style=flat-square)

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

The defaults are `gpt-image-2.5`, `16:9`, and `1K`. You can ask for another aspect ratio or resolution.

Note: the `--image-size` tier is model-dependent — `gpt-image-2-vip` honors 2K/4K (measured 2048x1152 / 3840x2160 at 16:9), while `gpt-image-2.5` and `gpt-image-2` ignore it (fixed ~1672x940 at 16:9). Ask for `gpt-image-2-vip` or `nano-banana-pro` when you need 2K/4K.

Each image is submitted separately. Generating several images may result in several charges.

## 5. Where images are saved

Generated images are archived by date automatically:

- Inside a project: `<project>/output/images/YYYY-MM-DD/`
- Outside any project: `~/Pictures/AI-generates-images/YYYY-MM-DD/` (visible in the macOS Finder and Windows File Explorer pictures folders)

Filenames look like `260917-1645-001-space-helmet-cat-cycling.png` (timestamp-sequence-content), with a matching `.md` recording the model, size and full prompt. You can also pass an explicit output directory.
