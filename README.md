<div align="center">

# Relay ImageGen

**在 Codex 和 Claude Code 中通过 Codex666 AI 媒体 API 生成图片**

![Agents](https://img.shields.io/badge/agents-Codex%20%7C%20Claude%20Code-202124?style=flat-square)
![Provider](https://img.shields.io/badge/provider-Codex666%20AI-2563EB?style=flat-square)
![Model](https://img.shields.io/badge/model-gpt--image--2-16A34A?style=flat-square)

[GitHub 仓库](https://github.com/yfpgle-glitch/relay-imagegen)

</div>

---

## 安装 Skill

需要 Python 3。没有的话，可以直接让 Codex 或 Claude Code 帮你安装。

把这句话发给 Codex 或 Claude Code：

```text
请把这个仓库根目录作为 Skill 安装：
https://github.com/yfpgle-glitch/relay-imagegen
```

安装后，如果没有识别，重新打开一个任务或会话。

## 配置 Provider

环境变量优先于本地 Key 文件。

| Provider | 环境变量 | 本地 Key 文件 |
|---|---|---|
| Codex666 AI | `CODEX666AI_API_KEY` | `~/.config/codex666ai/api_key` |

可以直接让当前工具安全配置，例如：

```text
帮我配置 relay-imagegen 的 Codex666 AI API Key。使用隐藏输入，
写入 ~/.config/codex666ai/api_key，不要在聊天中显示 Key。
```

API Key 不应发送到聊天中，也不要提交到 Git 仓库。

## 使用

明确说出 `relay-imagegen` 或 Codex666 AI：

- `使用 Codex666 AI 默认模型生成一张图片。`
- `使用 Codex666 AI 的 nano-banana-pro 生成 2K 图片。`
- `检查 Codex666 AI 当前可用的图片模型，不要生成图片。`

支持 8 个图片模型的文本生成。默认模型为 `gpt-image-2` 1K；其余模型可提供 2K 或 4K。执行前自动读取当前 Key 的模型目录并询价；视频不接入。

## Provider

| 标识 | 接口 | 能力 |
|---|---|---|
| `codex666ai` | Codex666 Media API | 默认 `gpt-image-2` 1K，以及 Firefly、FLUX、Nano Banana、Imagine 图片生成 |

生成通常会产生费用。执行前会读取当前 Key 可用模型并询价。最新验证结果和完整参数见 [`SKILL.md`](SKILL.md)。

## 使用边界

`relay-imagegen` 是 Codex666 AI 的专用执行器，不是默认的第三方生图工具。

- 明确指定 `relay-imagegen` 或 Codex666 AI 时使用它。
- 只说“用第三方工具生图”但没有指定 Provider 时，由 [`rightcode-image`](https://github.com/yfpgle-glitch/right-code-imagegen) 处理。
- 每次生成都可能产生费用，需要用户明确授权。
