<div align="center">

# Relay ImageGen

**在 Codex 和 Claude Code 中通过第三方 Relay 生成、修改和局部编辑图片**

![Agents](https://img.shields.io/badge/agents-Codex%20%7C%20Claude%20Code-202124?style=flat-square)
![Providers](https://img.shields.io/badge/providers-1pkapi%20%7C%20CallAI%20%7C%20Codex666%20AI-2563EB?style=flat-square)
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

每家服务使用独立的 API Key。环境变量优先于本地 Key 文件。

| Provider | 标识 | 环境变量 | 本地 Key 文件 |
|---|---|---|---|
| 皓悦API | `1pkapi` | `ONEPK_API_KEY` | `~/.config/1pkapi/api_key` |
| CallAI | `callai` | `CALLAI_API_KEY` | `~/.config/callai/api_key` |
| Codex666 AI | `codex666ai` | `CODEX666AI_API_KEY` | `~/.config/codex666ai/api_key` |

可以直接让当前工具安全配置，例如：

```text
帮我配置 relay-imagegen 的 CallAI API Key。使用隐藏输入，
写入 ~/.config/callai/api_key，不要在聊天中显示 Key。
```

API Key 不应发送到聊天中，也不要提交到 Git 仓库。

## 使用

明确说出 `relay-imagegen` 或 Provider 名称：

- `使用 relay-imagegen 的 1pkapi 生成一张 16:9 的电影感图片。`
- `使用 CallAI 修改这张参考图，把主色改成蓝色。`
- `使用 Codex666 AI 生成一张图片。`
- `使用 relay-imagegen 和这张遮罩图做局部编辑。`
- `检查 CallAI 当前可用的图片模型，不要生成图片。`

支持文本生成、参考图编辑、遮罩编辑和多参考图输入。默认模型为 `gpt-image-2`；具体模型、分辨率、批量数量和输出格式以所选 Provider 的实际结果为准。

## Provider 路由

| 标识 | 接口 | 能力 |
|---|---|---|
| `1pkapi` | OpenAI-compatible Images | 默认 Relay；文本生成、参考图、遮罩和高分辨率输出 |
| `callai` | OpenAI-compatible Images | 文本生成、参考图、遮罩和高分辨率输出 |
| `codex666ai` | Codex666 OpenAI Images | `gpt-image-2` 文本生成和图片编辑 |

生成和编辑通常会产生费用。执行前会检查所选 Provider 的可用模型。最新验证结果和完整参数见 [`SKILL.md`](SKILL.md)。

## 使用边界

`relay-imagegen` 是专用 Relay 执行器，不是默认的第三方生图工具。

- 明确指定 `relay-imagegen`、某个 Relay，或需要遮罩编辑等 Relay 专属能力时使用它。
- 只说“用第三方工具生图”但没有指定 Provider 时，由 [`rightcode-image`](https://github.com/yfpgle-glitch/right-code-imagegen) 处理。
- 每次任务固定使用当前选定的 Provider；跨 Provider 重试和新增付费任务需要单独明确。
