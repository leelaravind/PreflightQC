"""Custom profile storage.

Writes are atomic (temp file, fsync, replace) so that a crash mid-save cannot corrupt a
profile the user has been building. Losing a client's delivery specification because the
machine lost power during a save is not an acceptable failure mode.

A custom profile can never take a shipped preset's id: shadowing a platform preset would
mean a report saying "Instagram Reels" while applying somebody's private rules.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from preflightqc.platform.paths import atomic_write_text, user_profiles_dir
from preflightqc.profiles.model import CustomProfile

#: Profile ids are generated, never derived from the display name: names are not unique,
#: not path-safe, and change when a user renames a profile.
_ID_PATTERN = re.compile(r"^custom_[0-9a-f]{12}$")


class ProfileError(RuntimeError):
    """A profile could not be read, written or imported."""


def new_profile_id() -> str:
    return f"custom_{uuid.uuid4().hex[:12]}"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def profile_path(profile_id: str, *, directory: Path | None = None) -> Path:
    return (directory or user_profiles_dir()) / f"{profile_id}.json"


def save(profile: CustomProfile, *, directory: Path | None = None) -> CustomProfile:
    """Persist a profile atomically, stamping the modified date."""
    stamped = replace(
        profile,
        created=profile.created or _timestamp(),
        modified=_timestamp(),
    )
    payload = json.dumps(stamped.to_dict(), indent=2, sort_keys=True)
    try:
        atomic_write_text(profile_path(stamped.profile_id, directory=directory), payload)
    except OSError as exc:
        raise ProfileError(f"could not save profile '{stamped.name}': {exc}") from exc
    return stamped


def load(path: Path) -> CustomProfile:
    """Load one profile document."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProfileError(f"could not read profile at {path}: {exc}") from exc
    if not isinstance(payload, dict) or "profile_id" not in payload or "name" not in payload:
        raise ProfileError(f"{path.name} is not a PreflightQC profile document")
    try:
        return CustomProfile.from_dict(payload)
    except (KeyError, ValueError) as exc:
        raise ProfileError(f"{path.name} is not a valid profile: {exc}") from exc


def load_all(*, directory: Path | None = None) -> tuple[list[CustomProfile], list[tuple[Path, str]]]:
    """Load every profile, returning the good ones and the reasons for the bad ones."""
    folder = directory or user_profiles_dir()
    profiles: list[CustomProfile] = []
    rejected: list[tuple[Path, str]] = []
    if not folder.is_dir():
        return profiles, rejected
    for path in sorted(folder.glob("*.json")):
        try:
            profiles.append(load(path))
        except ProfileError as exc:
            rejected.append((path, str(exc)))
    return profiles, rejected


def delete(profile_id: str, *, directory: Path | None = None) -> bool:
    path = profile_path(profile_id, directory=directory)
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise ProfileError(f"could not delete profile: {exc}") from exc
    return True


def export_to(profile: CustomProfile, destination: Path) -> Path:
    """Write a profile to an arbitrary location, for handing to a collaborator."""
    try:
        atomic_write_text(destination, json.dumps(profile.to_dict(), indent=2, sort_keys=True))
    except OSError as exc:
        raise ProfileError(f"could not export profile: {exc}") from exc
    return destination


def import_from(
    source: Path,
    *,
    directory: Path | None = None,
    reserved_ids: frozenset[str] = frozenset(),
) -> CustomProfile:
    """Import a profile file, re-iding it on any collision.

    Re-iding rather than refusing means a freelancer receiving two profiles from
    different agencies never has to hand-edit JSON to use both.
    """
    profile = load(source)
    folder = directory or user_profiles_dir()
    taken = {p.profile_id for p in load_all(directory=folder)[0]} | set(reserved_ids)

    if profile.profile_id in taken or not _ID_PATTERN.match(profile.profile_id):
        profile = replace(profile, profile_id=new_profile_id())

    return save(profile, directory=folder)
