"""Shared project-local layout for generated-image skills."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from pathlib import Path
from typing import Any, Mapping
import unicodedata


PROJECT_MARKERS = (
    ".git",
    ".hg",
    "AGENTS.md",
    "CLAUDE.md",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "composer.json",
    "Gemfile",
    "project.config.json",
)
MAX_SLUG_LENGTH = 48


class ImageOutputLayoutError(RuntimeError):
    """Raised when a default project-local image location cannot be determined."""


def find_project_root(start_dir: Path | None = None, home: Path | None = None) -> Path | None:
    """Find the nearest marked project root without treating the home directory as one."""
    current = (Path.cwd() if start_dir is None else start_dir).expanduser().resolve()
    home_dir = (Path.home() if home is None else home).expanduser().resolve()
    for candidate in (current, *current.parents):
        if candidate == home_dir:
            break
        if any((candidate / marker).exists() for marker in PROJECT_MARKERS):
            return candidate
    return None


def content_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").strip()
    characters: list[str] = []
    for character in normalized:
        if character.isalnum():
            characters.append(character)
        else:
            characters.append("-")
    cleaned = re.sub(r"-+", "-", "".join(characters)).strip("-.")
    return cleaned[:MAX_SLUG_LENGTH].rstrip("-.") or "image"


def _markdown_value(value: Any) -> str:
    return str(value).replace("\n", " ").strip()


@dataclass(frozen=True)
class ImageOutputLayout:
    images_dir: Path
    prompts_dir: Path
    task_dir: Path
    timestamp: datetime
    managed_root: Path | None = None

    @property
    def date_label(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d")

    @property
    def name_prefix(self) -> str:
        return self.timestamp.strftime("%Y%m%d-%H%M%S")

    def prepare(self) -> None:
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.task_dir.mkdir(parents=True, exist_ok=True)
        if self.managed_root is not None:
            ignore = self.managed_root / ".gitignore"
            if not ignore.exists():
                ignore.write_text("# Generated image artifacts; move approved assets into the project manually.\n*\n!.gitignore\n", encoding="utf-8")

    def next_image_path(self, prompt: str, suffix: str) -> Path:
        slug = content_slug(prompt)
        sequence = 1
        while True:
            stem = f"{self.name_prefix}-{sequence:03d}-{slug}"
            image = self.images_dir / f"{stem}{suffix}"
            prompt_file = self.prompts_dir / f"{stem}.md"
            if not image.exists() and not prompt_file.exists():
                return image
            sequence += 1

    def save_image(self, content: bytes, suffix: str, prompt: str, metadata: Mapping[str, Any]) -> Path:
        self.prepare()
        image = self.next_image_path(prompt, suffix)
        image.write_bytes(content)
        self.write_prompt(image, prompt, metadata)
        return image

    def write_prompt(self, image: Path, prompt: str, metadata: Mapping[str, Any]) -> Path:
        self.prepare()
        prompt_file = self.prompts_dir / f"{image.stem}.md"
        lines = [f"# {image.stem}", ""]
        for label, key in (("服务商", "provider"), ("模型", "model"), ("尺寸", "size"), ("质量", "quality"), ("操作", "operation"), ("生成时间", "generated_at")):
            value = metadata.get(key)
            if value is not None and _markdown_value(value):
                lines.append(f"- {label}: {_markdown_value(value)}")
        lines.extend(["", "## 提示词", "", prompt.strip(), ""])
        prompt_file.write_text("\n".join(lines), encoding="utf-8")
        return prompt_file


def resolve_layout(
    output_dir: Path | None = None,
    *,
    cwd: Path | None = None,
    now: datetime | None = None,
    task_namespace: str,
) -> ImageOutputLayout:
    timestamp = now or datetime.now()
    if output_dir is not None:
        images_dir = output_dir.expanduser().resolve()
        return ImageOutputLayout(
            images_dir=images_dir,
            prompts_dir=images_dir / ".prompts",
            task_dir=images_dir / ".tasks" / task_namespace,
            timestamp=timestamp,
        )
    project_root = find_project_root(cwd)
    if project_root is None:
        raise ImageOutputLayoutError(
            "No project root was found. Run this command from a project directory or pass --output-dir explicitly."
        )
    root = project_root / "generated_images"
    return ImageOutputLayout(
        images_dir=root / "images" / timestamp.strftime("%Y-%m-%d"),
        prompts_dir=root / "prompts" / timestamp.strftime("%Y-%m-%d"),
        task_dir=root / ".tasks" / task_namespace,
        timestamp=timestamp,
        managed_root=root,
    )
