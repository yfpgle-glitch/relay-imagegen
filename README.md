<div align="center">

# relay-imagegen

**在 Codex、Claude Code 和 WorkBuddy 中，通过 RC 生成和修改图片**

**RC（Right Code）** 是一个中转站：[rightapi.ai](https://www.rightapi.ai) 提供的 AI 生图 API 服务，中转 `gpt-image`、`nano-banana` 等模型。生图 **低至 $0.04/张**（默认模型 $0.06/张，充值 1$ = ¥1.00），价格以 RC 后台为准。说 **RC** 就行。

![Agents](https://img.shields.io/badge/agents-Codex%20%7C%20Claude%20Code%20%7C%20WorkBuddy-202124?style=flat-square)
![Provider](https://img.shields.io/badge/provider-RC%20%28Right%20Code%29-2563EB?style=flat-square)
![Model](https://img.shields.io/badge/model-gpt--image--2.5--flare-16A34A?style=flat-square)

[GitHub 仓库](https://github.com/yfpgle-glitch/relay-imagegen) · 中文 · [English](README_EN.md)

</div>

---

## 一、安装 Skill

需要 Python 3。没有的话，可以直接让 Codex、Claude Code 或 WorkBuddy 帮你安装。

### 1、Codex / Claude Code

把这句话发给 Codex 或 Claude Code：

```text
请把这个仓库根目录作为 Skill 安装：
https://github.com/yfpgle-glitch/relay-imagegen
```

安装后，如果没有识别，重新打开一个任务或会话。

### 2、WorkBuddy

1. [下载 Skill 压缩包](https://github.com/yfpgle-glitch/relay-imagegen/archive/refs/heads/main.zip)。
2. 在 WorkBuddy 中打开“添加技能”，选择“上传技能”。
3. 上传刚刚下载的压缩包。

## 二、创建 API Key

1. [注册 RC（Right Code）](https://www.rightapi.ai/register?aff=9ec111f0) 并登录。（使用此链接注册，每次充值均可赠送 5% 额外额度。）
2. 打开“令牌管理”。
3. 点击“创建密钥”。

不知道怎么操作，可以查看 [RC 官方 API Key 教程](https://docs.rightapi.ai/docs/rc_quick_start/apikey.html)。

## 三、配置 API Key

安装完成后，对 Codex、Claude Code 或 WorkBuddy 说：

```text
帮我配置 RC API Key。
```

工具会打开一个隐藏输入框。粘贴 API Key，然后确认。输入时不会显示 Key。

## 四、使用

直接告诉当前工具你想要什么：

- `用 RC 生成一张电影感的 16:9 图片。`
- `用 RC 修改这张图片。`
- `用 RC 生成三种不同方案。`
- `继续处理 RC 任务 task_example。`

默认使用 `gpt-image-2.5-flare` 和 `16:9`（脚本转换为 `1536x864`），质量由服务端 `auto` 决定。精细编辑、多图融合或文字细节优先时，选 `gpt-image-2.5-sunburst`。

GPT 模型可以直接指定像素尺寸，例如 `--size 2048x1152 --quality xhigh`；`xhigh` / `max` 仅限两个 2.5 模型。原来的比例写法仍可用：`--size 16:9 --image-size 2K` 转为 `2048x1152`，`4K` 转为 `3840x2160`。显式像素尺寸不与 `--image-size` 同用；超过 `2560x1440` 的尺寸在 RC 中仍属于实验性大图。

Gemini 使用 `--model gemini-3-pro-image-preview` 或 `gemini-nano-banana-2.1`，通过 `--size 16:9 --image-size 2K` 指定比例和档位。参考图统一用 `--reference /absolute/path/image.png`，脚本按模型选择对应的编辑协议。

RC 暂不支持透明背景、mask 局部重绘和图片变体。局部修改请在提示词中说明。

每张图片会单独提交。一次生成多张图片，可能产生多次费用。

## 五、图片存放在哪

生成的图片自动按日期归档：

- 在项目内运行：`<项目>/output/images/YYYY-MM-DD/`
- 在项目外运行：`~/Pictures/AI-generates-images/YYYY-MM-DD/`（macOS Finder、Windows 资源管理器的图片文件夹下均可见）

文件名形如 `260917-1645-001-space-helmet-cat-cycling.png`（日期时间-序号-内容），同名 `.md` 记录模型、尺寸和完整提示词。也可以显式指定输出目录。

## 六、模型与价格

生图按次计费，充值单价 1$ = ¥1.00。下表价格参考 2026-09 版价目，模型改版后可能调整，**实际以 RC 后台为准**：

| 模型 | 价格 | 说明 |
|---|---:|---|
| `gpt-image-2` | $0.04/次 | 基础模型，固定尺寸，质量最高 `high`，最低价 |
| `gpt-image-2.5-flare` | $0.06/次 | **默认模型**，日常生图、速度优先 |
| `gpt-image-2.5-sunburst` | 待确认 | 精细编辑、多图融合、文字和细节；旧价目无对应项 |
| `gemini-nano-banana-2.1` | $0.12/次 | Nano Banana 2 系列，速度优先（旧 `nano-banana-2`） |
| `gemini-3-pro-image-preview` | $0.18/次 | Nano Banana Pro，画质和理解优先（旧 `nano-banana-pro`） |

价格来源与变化说明：

- 参考价取自 2026-09-17 版价目，旧模型名对应关系为：`gpt-image-2` $0.04、`gpt-image-2.5` $0.06（默认）、`nano-banana-2` $0.12、`gpt-image-2-vip` $0.13、`nano-banana-pro` $0.18、`nano-banana-2-lite` $0.05。
- `gpt-image-2.5-flare` 承接旧默认模型 `gpt-image-2.5` 的价格；`gpt-image-2.5-sunburst` 是同期新增的高质量档，旧价目里没有对应项，需在 RC 后台确认。
- 旧 `gpt-image-2-vip`（$0.13/次，支持 2K/4K）和 `nano-banana-2-lite`（$0.05/次）在当前模型清单里没有直接后继；需要 2K/4K 时按后台当前可用模型选。
- 日常生图用默认的 `gpt-image-2.5-flare` 即可。

旧模型名及旧的固定尺寸结论不再作为当前调用依据。每次任务的费用和账号可用模型以 RC 后台为准；[官方画图文档](https://docs.rightapi.ai/docs/rc_draw/) 说明了现行接口与参数。
