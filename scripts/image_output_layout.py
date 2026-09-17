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


def pictures_root(home: Path) -> Path:
    """Personal library for generated images when no project root exists."""
    return home / "Pictures" / "AI-generates-images"


def find_project_root(start_dir: Path | None = None, home: Path | None = None) -> Path | None:
    """Prefer the nearest repository root, then a project marker; never use home."""
    current = (Path.cwd() if start_dir is None else start_dir).expanduser().resolve()
    home_dir = (Path.home() if home is None else home).expanduser().resolve()
    candidates = []
    for candidate in (current, *current.parents):
        if candidate == home_dir:
            break
        candidates.append(candidate)
    for candidate in candidates:
        if any((candidate / marker).exists() for marker in (".git", ".hg")):
            return candidate
    for candidate in candidates:
        if candidate == home_dir:
            break
        if any((candidate / marker).exists() for marker in PROJECT_MARKERS):
            return candidate
    return None


def content_slug(value: str) -> str:
    """Convert content to a safe, readable filename slug.

    Prefers ASCII: accented latin characters are transliterated (café -> cafe).
    Characters without an ASCII form (Chinese, Japanese, ...) are kept as-is.
    """
    normalized = unicodedata.normalize("NFKC", value or "").strip()

    characters: list[str] = []
    for character in normalized:
        if character.isascii() and (character.isalnum() or character in "-_"):
            characters.append(character.lower())
        elif character.isalnum():
            decomposed = unicodedata.normalize("NFKD", character)
            ascii_chars = "".join(c for c in decomposed if c.isascii() and c.isalnum())
            characters.append(ascii_chars.lower() if ascii_chars else character)
        elif character.isspace() or character in "-_":
            characters.append("-")

    cleaned = re.sub(r"-+", "-", "".join(characters)).strip("-.")
    result = cleaned[:MAX_SLUG_LENGTH].rstrip("-.")

    # If we end up with nothing usable, use a generic name
    return result if result else "image"


def _markdown_value(value: Any) -> str:
    return str(value).replace("\n", " ").strip()


@dataclass(frozen=True)
class ImageOutputLayout:
    images_dir: Path
    prompts_dir: Path
    task_dir: Path
    timestamp: datetime
    managed_root: Path | None = None
    provider: str = ""
    model: str = ""

    @property
    def date_label(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d")

    @property
    def name_prefix(self) -> str:
        return self.timestamp.strftime("%y%m%d-%H%M")

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

    def save_image(self, content: bytes, suffix: str, filename_slug: str, metadata: Mapping[str, Any], original_prompt: str = "") -> Path:
        """Save image with separate filename slug and original prompt for metadata."""
        self.prepare()
        image = self.next_image_path(filename_slug, suffix)
        image.write_bytes(content)
        prompt_to_save = original_prompt if original_prompt else filename_slug
        self.write_prompt(image, prompt_to_save, metadata)
        return image

    def write_prompt(self, image: Path, prompt: str, metadata: Mapping[str, Any]) -> Path:
        self.prepare()
        prompt_file = self.prompts_dir / f"{image.stem}.md"
        lines = [f"# {image.stem}", ""]
        for label, key in (
            ("服务商", "provider"),
            ("模型", "model"),
            ("尺寸", "size"),
            ("质量", "quality"),
            ("操作", "operation"),
            ("生成时间", "generated_at"),
        ):
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
    provider: str = "",
    model: str = "",
    home: Path | None = None,
) -> ImageOutputLayout:
    timestamp = now or datetime.now()
    home_dir = Path.home() if home is None else home
    if output_dir is not None:
        images_dir = output_dir.expanduser().resolve()
        return ImageOutputLayout(
            images_dir=images_dir,
            prompts_dir=images_dir / ".prompts",
            task_dir=images_dir / ".tasks" / task_namespace,
            timestamp=timestamp,
            provider=provider,
            model=model,
        )
    project_root = find_project_root(cwd, home=home_dir)
    if project_root is not None:
        root = project_root / "output" / "images"
    else:
        # Outside any project: use the personal pictures library instead of
        # refusing or guessing a random directory.
        root = pictures_root(home_dir)
    return ImageOutputLayout(
        images_dir=root / timestamp.strftime("%Y-%m-%d"),
        prompts_dir=root / ".prompts" / timestamp.strftime("%Y-%m-%d"),
        task_dir=root / ".tasks" / task_namespace,
        timestamp=timestamp,
        managed_root=root,
        provider=provider,
        model=model,
    )
