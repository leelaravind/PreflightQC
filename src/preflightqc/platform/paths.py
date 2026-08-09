"""Filesystem locations and path handling.

Two things this module exists to get right:

* **Windows long paths.** A deliverable buried under a client folder tree routinely
  exceeds 260 characters, and a QC tool that silently skips those files is worse than
  useless.
* **A clear boundary between what we read and what we write.** Source videos are
  read-only, always (spec 12.1). Everything PreflightQC writes goes under the user's
  local application data or a location they explicitly chose.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "PreflightQC"

#: Extensions offered as candidates when enumerating a folder. This is a *filter*, not
#: an authority: the container is always determined by the inspector, never by the name
#: (spec 8.2).
DEFAULT_VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".wmv", ".asf", ".flv",
        ".mpg", ".mpeg", ".m2v", ".m2ts", ".mts", ".ts", ".3gp", ".3g2", ".mxf",
        ".ogv", ".vob", ".dv", ".rm", ".divx",
    }
)


def application_root() -> Path:
    """The directory the application was installed into.

    When frozen this is the folder holding the executable; in development it is the
    repository root. Bundled binaries and shipped presets are resolved from here, never
    from PATH or the working directory.
    """
    if getattr(sys, "frozen", False):  # pragma: no cover - only true in a built bundle
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def bundled_binaries_dir() -> Path:
    """Where the shipped inspector binaries live."""
    root = application_root()
    packaged = root / "bin"
    return packaged if packaged.is_dir() else root / "third-party" / "bin"


def shipped_presets_dir() -> Path:
    return application_root() / "presets"


def user_data_dir() -> Path:
    """Per-user writable location for configuration, profiles and logs.

    Windows is the only V1 target, so the non-Windows branch exists purely so that
    development on another platform does not explode; it is never exercised in a
    shipped build.
    """
    if sys.platform != "win32":  # pragma: no cover - not a V1 target
        return Path.home() / f".{APP_NAME.lower()}"
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / "AppData" / "Local" / APP_NAME


def user_profiles_dir() -> Path:
    return user_data_dir() / "profiles"


def user_logs_dir() -> Path:
    return user_data_dir() / "logs"


def config_file() -> Path:
    return user_data_dir() / "config.json"


def ensure_user_dirs() -> None:
    """Create the writable locations if they do not exist."""
    for directory in (user_data_dir(), user_profiles_dir(), user_logs_dir()):
        directory.mkdir(parents=True, exist_ok=True)


def extended_path(path: Path) -> str:
    """Render a path in the form Windows APIs accept beyond MAX_PATH.

    Without the \\\\?\\ prefix, a path over 260 characters fails to open on many Windows
    configurations. UNC paths need the separate \\\\?\\UNC\\ form.
    """
    if sys.platform != "win32":  # pragma: no cover - Windows is the V1 target
        return str(path)
    text = str(path)
    if text.startswith("\\\\?\\"):
        return text
    if not os.path.isabs(text):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text[2:]
    return "\\\\?\\" + text


def is_long_path(path: Path) -> bool:
    return len(str(path)) >= 260


def safe_resolve(path: Path) -> Path:
    """Resolve a path without raising on a broken link or a vanished file."""
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError):  # pragma: no cover - defensive
        return path.absolute()


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write a file atomically: temp file in the same directory, then replace.

    A crash mid-save must never corrupt an existing custom profile or config
    (architecture section 8).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with temp.open("w", encoding=encoding, newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            try:
                temp.unlink()
            except OSError:  # pragma: no cover - defensive
                pass


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with temp.open("wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            try:
                temp.unlink()
            except OSError:  # pragma: no cover - defensive
                pass
