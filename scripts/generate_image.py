#!/usr/bin/env python3
"""Generate images through Right Code's asynchronous draw API."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from dataclasses import dataclass, replace
from pathlib import Path
import re
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from image_output_layout import (
    ImageOutputLayout,
    content_slug,
    resolve_layout,
    find_project_root,
)


SUBMIT_URL = "https://www.rightapi.ai/draw/v1/images/generations"
TASK_URL = "https://www.rightapi.ai/v1/tasks/{task_id}"
AUTHENTICATED_DOWNLOAD_HOSTS = ("rightapi.ai", "right.codes")
DEFAULT_KEY_PATH = Path.home() / ".config/right-code/api_key"
IN_PROGRESS = {"queued", "pending", "processing", "in_progress"}
FAILED = {"failed", "error", "cancelled", "canceled"}
USER_AGENT = "rightcode-image-skill/2.0"
DEFAULT_POLL_RETRIES = 5
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}


class RightCodeError(RuntimeError):
    """A safe, user-facing Right Code client error.

    kind carries the recovery policy documented in SKILL.md so agents branch
    on machine-readable output instead of matching message strings.
    checkpoint points at the task record saved before raising, when one exists.
    """

    kind = "error"

    def __init__(self, message: str, *, checkpoint: Optional[str] = None):
        super().__init__(message)
        self.checkpoint = checkpoint


class AuthenticationError(RightCodeError):
    kind = "auth_error"


class SubmissionAmbiguousError(RightCodeError):
    kind = "submission_ambiguous"


class TransientPollError(RightCodeError):
    kind = "transient_poll"


class PollTimeoutError(RightCodeError):
    kind = "poll_timeout"


class TaskFailedError(RightCodeError):
    kind = "task_failed"


class UnknownStatusError(RightCodeError):
    kind = "unknown_status"


class BadResponseError(RightCodeError):
    kind = "bad_response"


class HttpError(RightCodeError):
    kind = "http_error"


RETRYABLE_KINDS = frozenset({"transient_poll", "poll_timeout"})


def read_api_key(
    env: Optional[Dict[str, str]] = None,
    key_path: Path = DEFAULT_KEY_PATH,
) -> str:
    source = os.environ if env is None else env
    api_key = source.get("RIGHT_CODES_API_KEY", "").strip()
    if not api_key and key_path.is_file():
        api_key = key_path.read_text(encoding="utf-8").strip()
    if not api_key:
        raise AuthenticationError(
            "Right Code API key is missing. Put it in "
            f"{key_path} or set RIGHT_CODES_API_KEY for this process."
        )
    return api_key


def _provider_message(body: bytes, fallback: str) -> str:
    if not body:
        return fallback
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = body.decode("utf-8", errors="replace").strip()
        return text[:500] or fallback
    if isinstance(value, dict):
        error = value.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        for key in ("message", "detail", "error"):
            if isinstance(value.get(key), str):
                return value[key]
    return fallback


def format_http_error(
    stage: str,
    method: str,
    url: str,
    status: int,
    body: bytes,
) -> str:
    path = urlparse(url).path or "/"
    message = _provider_message(body, f"HTTP {status}")
    return f"Right Code {stage} failed: {method} {path} -> HTTP {status}: {message}"


class UrlLibTransport:
    def __init__(self, request_timeout: float = 60.0):
        self.request_timeout = request_timeout

    def request_json(
        self,
        method: str,
        url: str,
        api_key: str,
        payload: Optional[Dict[str, Any]] = None,
        stage: str = "request",
    ) -> Dict[str, Any]:
        data = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": USER_AGENT,
        }
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.request_timeout) as response:
                body = response.read()
        except HTTPError as exc:
            body = exc.read()
            if exc.code in (401, 403):
                raise AuthenticationError(
                    format_http_error(stage, method, url, exc.code, body)
                ) from exc
            if exc.code >= 500 and stage == "poll":
                raise TransientPollError(
                    format_http_error(stage, method, url, exc.code, body)
                ) from exc
            raise HttpError(
                format_http_error(stage, method, url, exc.code, body)
            ) from exc
        except OSError as exc:
            # URLError covers connection failures; a read timeout after the
            # connection is established raises a bare TimeoutError instead.
            path = urlparse(url).path or "/"
            reason = getattr(exc, "reason", exc)
            if stage == "submit":
                # The request may or may not have reached the provider, so a
                # resubmission could double-charge; never auto-retry here.
                raise SubmissionAmbiguousError(
                    f"Right Code {stage} network error: {method} {path} -> {reason}"
                ) from exc
            if stage == "poll":
                raise TransientPollError(
                    f"Right Code {stage} network error: {method} {path} -> {reason}"
                ) from exc
            raise RightCodeError(
                f"Right Code {stage} network error: {method} {path} -> {reason}"
            ) from exc
        try:
            parsed = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            path = urlparse(url).path or "/"
            raise BadResponseError(
                f"Right Code {stage} returned invalid JSON for {method} {path}."
            ) from exc
        if not isinstance(parsed, dict):
            raise BadResponseError(
                f"Right Code {stage} returned an unexpected JSON value."
            )
        return parsed

    def download(self, url: str, api_key: str) -> Tuple[bytes, str]:
        headers = {"Accept": "image/*", "User-Agent": USER_AGENT}
        hostname = (urlparse(url).hostname or "").lower()
        if any(
            hostname == domain or hostname.endswith(f".{domain}")
            for domain in AUTHENTICATED_DOWNLOAD_HOSTS
        ):
            headers["Authorization"] = f"Bearer {api_key}"
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self.request_timeout) as response:
                content_type = response.headers.get_content_type()
                return response.read(), content_type
        except HTTPError as exc:
            body = exc.read()
            if exc.code in (401, 403):
                raise AuthenticationError(
                    format_http_error("download", "GET", url, exc.code, body)
                ) from exc
            if exc.code >= 500:
                raise TransientPollError(
                    format_http_error("download", "GET", url, exc.code, body)
                ) from exc
            raise HttpError(
                format_http_error("download", "GET", url, exc.code, body)
            ) from exc
        except OSError as exc:
            # Same as request_json: read timeouts arrive as bare TimeoutError.
            # A failed download is recoverable by resuming the same task.
            path = urlparse(url).path or "/"
            reason = getattr(exc, "reason", exc)
            raise TransientPollError(
                f"Right Code download network error: GET {path} -> {reason}"
            ) from exc


def _reference_data_url(path: Path) -> str:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise RightCodeError(f"Reference image does not exist: {path}")
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith("image/"):
        raise RightCodeError(f"Unsupported reference image type: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_payload(
    prompt: str,
    model: str,
    count: int,
    size: Optional[str],
    image_size: Optional[str],
    reference_paths: Sequence[Path],
) -> Dict[str, Any]:
    if count != 1:
        raise RightCodeError(
            "Right Code provider tasks must request a single image; "
            "use batch count to create multiple independent tasks."
        )
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "n": count,
        "async": True,
    }
    if size:
        payload["size"] = size
    if image_size:
        payload["imageSize"] = image_size
    if reference_paths:
        payload["image"] = [_reference_data_url(path) for path in reference_paths]
    return payload


def _collect_image_values(value: Any, context_key: str = "") -> Iterable[Tuple[str, str, str]]:
    if isinstance(value, list):
        for item in value:
            yield from _collect_image_values(item, context_key)
        return
    if isinstance(value, str):
        if context_key == "text" and value.startswith(("https://", "http://")):
            yield "url", value, ""
        return
    if not isinstance(value, dict):
        return

    url = value.get("url")
    if isinstance(url, str) and url.startswith(("https://", "http://")):
        yield "url", url, ""
    encoded = value.get("b64_json")
    if isinstance(encoded, str):
        yield "base64", encoded, "image/png"
    inline_data = value.get("inlineData") or value.get("inline_data")
    if isinstance(inline_data, dict) and isinstance(inline_data.get("data"), str):
        mime_type = inline_data.get("mimeType") or inline_data.get("mime_type") or "image/png"
        yield "base64", inline_data["data"], str(mime_type)

    for key in ("data", "candidates", "result", "results", "output", "images", "parts", "content"):
        if key in value:
            yield from _collect_image_values(value[key], key)
    if "text" in value:
        yield from _collect_image_values(value["text"], "text")


def _safe_task_id(task_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("-.")
    return cleaned or "task"


def _extension(content_type: str, url: str = "") -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return ".jpg" if suffix == ".jpeg" else suffix
    return {
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/avif": ".avif",
    }.get(content_type.lower(), ".png")


def _validate_image_bytes(content: bytes, content_type: str) -> None:
    signatures = (
        content.startswith(b"\x89PNG\r\n\x1a\n"),
        content.startswith(b"\xff\xd8\xff"),
        content.startswith((b"GIF87a", b"GIF89a")),
        len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP",
        len(content) >= 12 and content[4:12] in {b"ftypavif", b"ftypavis"},
    )
    if not content:
        raise BadResponseError("Right Code returned an empty image file.")
    if not any(signatures) and not content_type.lower().startswith("image/"):
        raise BadResponseError(
            f"Right Code returned non-image content ({content_type or 'unknown type'})."
        )


def _decode_base64(value: str) -> bytes:
    if value.startswith("data:"):
        _, separator, value = value.partition(",")
        if not separator:
            raise BadResponseError("Right Code returned an invalid image data URL.")
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise BadResponseError("Right Code returned invalid base64 image data.") from exc


def _write_checkpoint(
    task_dir: Path,
    task_id: str,
    status: str,
    model: str,
    **extra: Any,
) -> Path:
    task_dir = task_dir.expanduser().resolve()
    task_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = task_dir / f"right-code-task-{_safe_task_id(task_id)}.json"
    # Later writes (resuming/completed/...) must keep fields such as prompt
    # and size recorded by earlier writes; resume reads them back.
    previous: Dict[str, Any] = {}
    if checkpoint.is_file():
        try:
            loaded = json.loads(checkpoint.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            loaded = None
        if isinstance(loaded, dict):
            previous = loaded
    payload = {
        **previous,
        "task_id": task_id,
        "status": status,
        "model": model,
        "updated_at": int(time.time()),
        **extra,
    }
    temporary = checkpoint.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(checkpoint)
    return checkpoint


def _checkpoint_value(task_dir: Path, task_id: str, key: str) -> Optional[str]:
    checkpoint = (
        task_dir.expanduser().resolve()
        / f"right-code-task-{_safe_task_id(task_id)}.json"
    )
    if not checkpoint.is_file():
        return None
    try:
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    value = payload.get(key) if isinstance(payload, dict) else None
    return value.strip() if isinstance(value, str) and value.strip() else None


def _checkpoint_filename_stem(task_dir: Path, task_id: str) -> Optional[str]:
    value = _checkpoint_value(task_dir, task_id, "filename_stem")
    return content_slug(value) if value else None


def _save_results(
    values: Sequence[Tuple[str, str, str]],
    api_key: str,
    transport: Any,
    layout: ImageOutputLayout,
    filename_stem: Optional[str] = None,
    prompt: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> List[str]:
    files: List[str] = []
    for kind, value, declared_type in values:
        if kind == "url":
            content, content_type = transport.download(value, api_key)
            suffix = _extension(content_type, value)
        else:
            content = _decode_base64(value)
            content_type = declared_type or "image/png"
            suffix = _extension(content_type)
        _validate_image_bytes(content, content_type)
        # filename_stem wins when the user supplied one; otherwise name by prompt
        name_source = filename_stem or prompt
        path = layout.save_image(content, suffix, name_source, metadata or {}, original_prompt=prompt)
        files.append(str(path))
    return files


def _task_error_message(task: Dict[str, Any]) -> str:
    error = task.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        return error["message"]
    if isinstance(error, str):
        return error
    if isinstance(task.get("message"), str):
        return task["message"]
    return "Right Code image task failed."


@dataclass(frozen=True)
class RunSpec:
    """Everything one run needs besides the request payload and api key."""

    output_dir: Path
    layout: ImageOutputLayout
    task_dir: Optional[Path] = None
    poll_interval: float = 3.0
    timeout: float = 600.0
    poll_retries: int = DEFAULT_POLL_RETRIES
    filename_stem: Optional[str] = None


def poll_task(
    api_key: str,
    task_id: str,
    spec: RunSpec,
    *,
    model: str,
    prompt: str = "",
    size_label: str = "",
    initial_task: Optional[Dict[str, Any]] = None,
    transport: Optional[Any] = None,
    sleep: Any = time.sleep,
    monotonic: Any = time.monotonic,
) -> Dict[str, Any]:
    if spec.poll_interval < 0:
        raise RightCodeError("Poll interval cannot be negative.")
    if spec.timeout <= 0:
        raise RightCodeError("Timeout must be greater than zero.")
    if spec.poll_retries < 0:
        raise RightCodeError("Poll retries cannot be negative.")
    if not task_id:
        raise RightCodeError("Right Code task ID is required.")
    transport = transport or UrlLibTransport()
    task_dir = spec.task_dir or spec.output_dir
    task = initial_task or {"task_id": task_id, "status": "pending"}
    image_stem = content_slug(spec.filename_stem or "right-code")
    image_metadata = {
        "provider": "Right Code",
        "model": model,
        "size": size_label,
        "operation": "generation",
        "generated_at": spec.layout.timestamp.isoformat(sep=" ", timespec="seconds"),
    }

    started = monotonic()
    consecutive_poll_errors = 0
    next_delay = spec.poll_interval
    while True:
        values = list(_collect_image_values(task))
        if values:
            files = _save_results(
                values,
                api_key,
                transport,
                spec.layout,
                filename_stem=image_stem,
                prompt=prompt,
                metadata=image_metadata,
            )
            checkpoint = _write_checkpoint(
                task_dir,
                task_id,
                "completed",
                model,
                filename_stem=image_stem,
                files=files,
            )
            return {
                "task_id": task_id,
                "status": "completed",
                "files": files,
                "checkpoint": str(checkpoint),
            }

        status = str(task.get("status") or "").lower()
        if status == "completed":
            checkpoint = _write_checkpoint(
                task_dir,
                task_id,
                "completed_without_image",
                model,
                filename_stem=image_stem,
            )
            raise BadResponseError(
                "Right Code poll completed but returned no image URL or base64 data; "
                f"checkpoint: {checkpoint}",
                checkpoint=str(checkpoint),
            )
        if status in FAILED:
            message = _task_error_message(task)
            checkpoint = _write_checkpoint(
                task_dir,
                task_id,
                "failed",
                model,
                filename_stem=image_stem,
                error=message,
            )
            raise TaskFailedError(
                f"Right Code task failed: {message}; checkpoint: {checkpoint}",
                checkpoint=str(checkpoint),
            )
        if status and status not in IN_PROGRESS:
            checkpoint = _write_checkpoint(
                task_dir,
                task_id,
                "unknown_status",
                model,
                filename_stem=image_stem,
                provider_status=status,
            )
            raise UnknownStatusError(
                f"Right Code poll returned unknown task status {status!r}; "
                f"checkpoint: {checkpoint}",
                checkpoint=str(checkpoint),
            )
        if monotonic() - started >= spec.timeout:
            checkpoint = _write_checkpoint(
                task_dir,
                task_id,
                "timed_out",
                model,
                filename_stem=image_stem,
            )
            raise PollTimeoutError(
                f"Right Code task timed out after {spec.timeout:g} seconds; "
                f"checkpoint: {checkpoint}",
                checkpoint=str(checkpoint),
            )

        sleep(next_delay)
        try:
            task = transport.request_json(
                "GET", TASK_URL.format(task_id=task_id), api_key, stage="poll"
            )
        except TransientPollError as exc:
            consecutive_poll_errors += 1
            if consecutive_poll_errors > spec.poll_retries:
                checkpoint = _write_checkpoint(
                    task_dir,
                    task_id,
                    "poll_error",
                    model,
                    filename_stem=image_stem,
                    error=str(exc),
                    attempts=consecutive_poll_errors,
                )
                raise TransientPollError(
                    f"{exc}; checkpoint: {checkpoint}",
                    checkpoint=str(checkpoint),
                ) from exc
            next_delay = min(
                max(spec.poll_interval, 1.0) * (2 ** (consecutive_poll_errors - 1)),
                30.0,
            )
            _write_checkpoint(
                task_dir,
                task_id,
                "poll_retrying",
                model,
                filename_stem=image_stem,
                error=str(exc),
                retry=consecutive_poll_errors,
                max_retries=spec.poll_retries,
            )
            continue
        except RightCodeError as exc:
            # Any other controlled failure (auth, task_failed, ...) stops
            # immediately; make sure the saved checkpoint is reachable.
            if exc.checkpoint is None:
                exc.checkpoint = str(
                    task_dir.expanduser().resolve()
                    / f"right-code-task-{_safe_task_id(task_id)}.json"
                )
            raise
        consecutive_poll_errors = 0
        next_delay = spec.poll_interval


def resume_task(
    api_key: str,
    task_id: str,
    spec: RunSpec,
    *,
    model: str = "gpt-image-2.5",
    transport: Optional[Any] = None,
    sleep: Any = time.sleep,
    monotonic: Any = time.monotonic,
) -> Dict[str, Any]:
    task_dir = spec.task_dir or spec.output_dir
    image_stem = content_slug(
        spec.filename_stem
        or _checkpoint_filename_stem(task_dir, task_id)
        or "right-code"
    )
    prompt = _checkpoint_value(task_dir, task_id, "prompt") or image_stem
    spec = replace(spec, filename_stem=image_stem)
    _write_checkpoint(
        task_dir,
        task_id,
        "resuming",
        model,
        filename_stem=image_stem,
    )
    return poll_task(
        api_key,
        task_id,
        spec,
        model=model,
        prompt=prompt,
        size_label=_checkpoint_value(task_dir, task_id, "size") or "",
        transport=transport,
        sleep=sleep,
        monotonic=monotonic,
    )


def generate(
    api_key: str,
    payload: Dict[str, Any],
    spec: RunSpec,
    *,
    transport: Optional[Any] = None,
    sleep: Any = time.sleep,
    monotonic: Any = time.monotonic,
) -> Dict[str, Any]:
    transport = transport or UrlLibTransport()
    model = str(payload.get("model") or "")
    task = transport.request_json(
        "POST", SUBMIT_URL, api_key, payload, stage="submit"
    )
    task_id = task.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise BadResponseError("Right Code submit response did not contain a task_id.")
    prompt = str(payload.get("prompt") or "")
    image_stem = content_slug(spec.filename_stem or prompt or "right-code")
    spec = replace(spec, filename_stem=image_stem)
    task_dir = spec.task_dir or spec.output_dir
    size_label = " ".join(
        str(part)
        for part in (payload.get("size"), payload.get("imageSize"))
        if part
    )
    _write_checkpoint(
        task_dir,
        task_id,
        "submitted",
        model,
        filename_stem=image_stem,
        prompt=prompt,
        size=size_label,
    )
    return poll_task(
        api_key,
        task_id,
        spec,
        model=model,
        prompt=prompt,
        size_label=size_label,
        initial_task=task,
        transport=transport,
        sleep=sleep,
        monotonic=monotonic,
    )


def generate_batch(
    api_key: str,
    payload: Dict[str, Any],
    spec: RunSpec,
    request_count: int,
    generate_one: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Run independent single-image tasks sequentially and aggregate their results."""
    if request_count < 1:
        raise RightCodeError("Batch count must be at least 1.")
    if payload.get("n") != 1:
        raise RightCodeError("Batch payload must keep provider field n fixed at 1.")

    runner = generate if generate_one is None else generate_one
    tasks: List[Dict[str, Any]] = []
    files: List[str] = []
    errors: List[Dict[str, Any]] = []

    for request_index in range(1, request_count + 1):
        single_payload = dict(payload)
        single_payload["n"] = 1
        try:
            result = runner(api_key, single_payload, spec)
        except RightCodeError as exc:
            message = str(exc)
            errors.append({"request": request_index, "message": message})
            tasks.append(
                {"request": request_index, "status": "failed", "error": message}
            )
            continue

        result_files = [
            str(path) for path in result.get("files", []) if isinstance(path, str)
        ]
        files.extend(result_files)
        tasks.append(
            {
                "request": request_index,
                "status": "completed",
                "task_id": result.get("task_id"),
                "files": result_files,
                "checkpoint": result.get("checkpoint"),
            }
        )

    completed = request_count - len(errors)
    if completed == request_count:
        status = "completed"
    elif completed == 0:
        status = "failed"
    else:
        status = "partial"
    return {
        "status": status,
        "requested": request_count,
        "completed": completed,
        "failed": len(errors),
        "files": files,
        "tasks": tasks,
        "errors": errors,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate images with Right Code."
    )
    parser.add_argument("--prompt", help="Image prompt (required for a new task)")
    parser.add_argument(
        "--resume-task-id",
        help="Resume polling an existing task without submitting a new paid task",
    )
    parser.add_argument(
        "--model", default="gpt-image-2.5", help="Right Code image model (default: gpt-image-2.5)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of independent single-image tasks to run sequentially (default: 1)",
    )
    parser.add_argument(
        "--size",
        default="16:9",
        help="Aspect ratio or pixel size (default: 16:9)",
    )
    parser.add_argument(
        "--image-size",
        choices=("1K", "2K", "4K"),
        default="1K",
        help="Model resolution (default: 1K)",
    )
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        type=Path,
        help="Reference image path; repeat for multiple images",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for generated image files; otherwise use the current project's output/images layout",
    )
    parser.add_argument(
        "--filename",
        help="Readable filename title without an extension (default: derived from prompt)",
    )
    parser.add_argument("--poll-interval", type=float, default=3.0)
    parser.add_argument(
        "--poll-retries",
        type=int,
        default=DEFAULT_POLL_RETRIES,
        help=f"Consecutive poll network retries (default: {DEFAULT_POLL_RETRIES})",
    )
    parser.add_argument("--timeout", type=float, default=600.0)
    return parser.parse_args(argv)


def restore_legacy_checkpoint(layout: ImageOutputLayout, task_id: str) -> None:
    """Copy a pre-migration checkpoint without creating a new provider task."""
    filename = f"right-code-task-{_safe_task_id(task_id)}.json"
    target = layout.task_dir / filename
    if target.exists():
        return
    project = find_project_root()
    if project is None:
        return
    current = Path.cwd().resolve()
    candidates = []
    for parent in (current, *current.parents):
        candidates.append(parent / "generated_images" / ".tasks" / "rightcode" / filename)
        if parent == project:
            break
    for source in candidates:
        if source.is_file():
            layout.task_dir.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            return


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parse_args(argv)
        layout = resolve_layout(args.output_dir, task_namespace="rightcode", provider="rightcode", model=args.model)
        layout.prepare()
        spec = RunSpec(
            output_dir=layout.images_dir,
            layout=layout,
            task_dir=layout.task_dir,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
            poll_retries=args.poll_retries,
            filename_stem=args.filename,
        )
        api_key = read_api_key()
        if args.resume_task_id:
            if args.prompt or args.reference or args.count != 1:
                raise RightCodeError(
                    "Resume mode cannot be combined with --prompt, --reference, or --count."
                )
            if args.output_dir is None:
                restore_legacy_checkpoint(layout, args.resume_task_id)
            result = resume_task(api_key, args.resume_task_id, spec, model=args.model)
        else:
            if not args.prompt:
                raise RightCodeError(
                    "--prompt is required unless --resume-task-id is provided."
                )
            payload = build_payload(
                prompt=args.prompt,
                model=args.model,
                count=1,
                size=args.size,
                image_size=args.image_size,
                reference_paths=args.reference,
            )
            if args.count == 1:
                result = generate(api_key, payload, spec)
            else:
                result = generate_batch(api_key, payload, spec, args.count)
    except RightCodeError as exc:
        error: Dict[str, Any] = {
            "status": "error",
            "kind": exc.kind,
            "message": str(exc),
        }
        if exc.checkpoint:
            error["checkpoint"] = exc.checkpoint
        print(json.dumps(error, ensure_ascii=False))
        return 3 if exc.kind in RETRYABLE_KINDS else 2
    print(json.dumps(result, ensure_ascii=False))
    return 2 if result.get("status") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
