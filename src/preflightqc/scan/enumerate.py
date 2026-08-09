"""File and folder enumeration.

Enumeration runs off the UI thread and is cancellable, because a deep folder on a slow
network share must never freeze the application (spec 8.2).

Extension matching is a **candidate filter only**. The authoritative container
determination always comes from the inspector, never from the filename -- a `.mov` that
is really a Matroska file is judged on what it is, not what it is called.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from preflightqc.platform.paths import DEFAULT_VIDEO_EXTENSIONS, safe_resolve

#: How deep a symlink or junction chain is followed. One level is enough for the common
#: "network drive mapped into a project folder" case without risking a cycle.
MAX_LINK_DEPTH = 1


@dataclass(frozen=True, slots=True)
class EnumerationOptions:
    recurse: bool = True
    include_hidden: bool = False
    extensions: frozenset[str] = DEFAULT_VIDEO_EXTENSIONS
    #: When False, every regular file is offered regardless of extension. Useful when a
    #: user knows their deliverable has an unusual name.
    filter_by_extension: bool = True


@dataclass(slots=True)
class EnumerationResult:
    files: list[Path] = field(default_factory=list)
    skipped_duplicates: int = 0
    skipped_by_extension: int = 0
    unreadable: list[tuple[Path, str]] = field(default_factory=list)
    cancelled: bool = False

    @property
    def count(self) -> int:
        return len(self.files)


def _is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    try:
        attrs = os.stat(path).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attrs & 2)  # FILE_ATTRIBUTE_HIDDEN


def _matches(path: Path, options: EnumerationOptions) -> bool:
    if not options.filter_by_extension:
        return True
    return path.suffix.lower() in options.extensions


def _walk(
    directory: Path,
    options: EnumerationOptions,
    result: EnumerationResult,
    should_cancel: Callable[[], bool],
    depth: int,
) -> Iterator[Path]:
    try:
        entries = sorted(directory.iterdir())
    except (OSError, PermissionError) as exc:
        result.unreadable.append((directory, str(exc)))
        return

    for entry in entries:
        if should_cancel():
            result.cancelled = True
            return
        try:
            is_dir = entry.is_dir()
            is_link = entry.is_symlink() or (is_dir and entry.is_junction())
        except OSError as exc:  # pragma: no cover - transient filesystem states
            result.unreadable.append((entry, str(exc)))
            continue

        if not options.include_hidden and _is_hidden(entry):
            continue

        if is_dir:
            if not options.recurse:
                continue
            if is_link and depth >= MAX_LINK_DEPTH:
                continue
            yield from _walk(
                entry, options, result, should_cancel, depth + (1 if is_link else 0)
            )
            if result.cancelled:
                return
            continue

        if _matches(entry, options):
            yield entry
        else:
            result.skipped_by_extension += 1


def enumerate_inputs(
    paths: Iterable[Path],
    *,
    options: EnumerationOptions | None = None,
    should_cancel: Callable[[], bool] = lambda: False,
) -> EnumerationResult:
    """Expand a mixed list of files and folders into a de-duplicated file list.

    De-duplication is by *resolved* path, so the same file reached through a symlink and
    directly is enqueued once.

    A file the user named explicitly is always included, even if its extension is not on
    the candidate list: they told us to check it, so we check it.
    """
    options = options or EnumerationOptions()
    result = EnumerationResult()
    seen: set[str] = set()

    def admit(path: Path) -> None:
        key = str(safe_resolve(path)).lower()
        if key in seen:
            result.skipped_duplicates += 1
            return
        seen.add(key)
        result.files.append(path)

    for raw_path in paths:
        if should_cancel():
            result.cancelled = True
            break
        path = Path(raw_path)
        try:
            if path.is_dir():
                for found in _walk(path, options, result, should_cancel, depth=0):
                    admit(found)
                if result.cancelled:
                    break
            elif path.is_file():
                # Explicitly named files bypass the extension filter by design.
                admit(path)
            else:
                result.unreadable.append((path, "path does not exist"))
        except (OSError, PermissionError) as exc:
            result.unreadable.append((path, str(exc)))

    return result
