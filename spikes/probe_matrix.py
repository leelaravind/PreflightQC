"""Phase 1 inspector spike harness (implementation plan section 2).

Runs both inspectors over an operator-supplied sample set and emits a coverage
matrix, so that the Phase 2 metadata model is built on measurement rather than
assumption.

This is spike code. It is NOT shipped, NOT imported by the application, and lives
outside `src/`.

Prerequisites (the operator supplies these; this script downloads nothing):
    third-party/bin/ffprobe.exe      unmodified BtbN win64-lgpl-shared
    third-party/bin/mediainfo.exe    MediaInfo >= 0.7.63 CLI (or MediaInfo.dll)
    spikes/samples/                  representative real media

Usage:
    python spikes/probe_matrix.py [--samples DIR] [--out FILE]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from preflightqc.platform.binaries import audit_configuration, licence_version

REPO_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = REPO_ROOT / "third-party" / "bin"
DEFAULT_SAMPLES = REPO_ROOT / "spikes" / "samples"

#: The build audit is NOT duplicated here. It delegates to the shipped implementation
#: in `preflightqc.platform.binaries`, so the spike and the application can never
#: disagree about whether a build is acceptable -- which they did, before this fix.

#: Every field the specification requires the normalised model to represent
#: (spec section 9). The spike records a determinability verdict for each.
REQUIRED_FIELDS = (
    "file.size",
    "file.duration",
    "container.format",
    "container.major_brand",
    "container.stream_count",
    "container.overall_bitrate",
    "container.faststart",
    "container.edit_lists_present",
    "video.codec",
    "video.profile",
    "video.level",
    "video.width",
    "video.height",
    "video.coded_width",
    "video.coded_height",
    "video.sample_aspect_ratio",
    "video.display_aspect_ratio",
    "video.rotation",
    "video.frame_rate",
    "video.frame_rate_mode",
    "video.bitrate",
    "video.pixel_format",
    "video.bit_depth",
    "video.chroma_subsampling",
    "video.scan_type",
    "video.colour_range",
    "video.colour_space",
    "video.transfer_characteristics",
    "video.colour_primaries",
    "video.gop_closed",
    "video.hdr_format",
    "video.dolby_vision",
    "audio.present",
    "audio.codec",
    "audio.sample_rate",
    "audio.channels",
    "audio.channel_layout",
    "audio.bitrate",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(argv: list[str], timeout: float = 60.0) -> tuple[int, str, str, float]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        return -1, "", "binary not found", 0.0
    except subprocess.TimeoutExpired:
        return -2, "", "timeout", time.monotonic() - started
    return (
        completed.returncode,
        completed.stdout,
        completed.stderr,
        (time.monotonic() - started) * 1000.0,
    )


def locate_binaries() -> dict[str, Path | None]:
    """Find the operator-supplied inspectors. Never consults PATH."""
    found: dict[str, Path | None] = {}
    for name, candidates in (
        ("ffprobe", ("ffprobe.exe", "ffprobe")),
        ("mediainfo", ("mediainfo.exe", "mediainfo", "MediaInfo.exe")),
    ):
        found[name] = next((BIN_DIR / c for c in candidates if (BIN_DIR / c).is_file()), None)
    return found


def audit_ffprobe_build(ffprobe: Path) -> dict[str, Any]:
    """GATE-1 — confirm the build is an acceptable LGPL shared build.

    Delegates to the same code the application runs at startup. Duplicating the
    policy here is how a spike and its product drift apart.
    """
    code, stdout, stderr, _ = _run([str(ffprobe), "-hide_banner", "-version"])
    text = f"{stdout}\n{stderr}"
    violations = audit_configuration(text)
    return {
        "exit_code": code,
        "version_output": text.strip(),
        "violations": list(violations),
        "licence": licence_version(text),
        "gate_1_pass": code == 0 and not violations,
        "sha256": _sha256(ffprobe),
    }


def probe_with_ffprobe(ffprobe: Path, sample: Path) -> dict[str, Any]:
    argv = [
        str(ffprobe),
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-show_error",
        str(sample),
    ]
    code, stdout, stderr, ms = _run(argv)
    try:
        payload = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"malformed json: {exc}", "exit_code": code, "ms": ms}
    return {"ok": code == 0, "exit_code": code, "ms": ms, "stderr": stderr[:500], "raw": payload}


def probe_with_mediainfo(mediainfo: Path, sample: Path) -> dict[str, Any]:
    argv = [str(mediainfo), "--Output=JSON", str(sample)]
    code, stdout, stderr, ms = _run(argv)
    try:
        payload = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"malformed json: {exc}", "exit_code": code, "ms": ms}
    return {"ok": code == 0, "exit_code": code, "ms": ms, "stderr": stderr[:500], "raw": payload}


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 inspector coverage spike")
    parser.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "spikes" / "probe-matrix.json")
    args = parser.parse_args()

    binaries = locate_binaries()
    missing = [name for name, path in binaries.items() if path is None]
    if missing:
        print(
            "GATE-1 BLOCKED: inspector binaries not present in third-party/bin/: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        print(
            "The operator must supply checksum-verified binaries. "
            "This script downloads nothing by design.",
            file=sys.stderr,
        )
        return 2

    ffprobe = binaries["ffprobe"]
    mediainfo = binaries["mediainfo"]
    assert ffprobe is not None and mediainfo is not None

    audit = audit_ffprobe_build(ffprobe)
    if not audit["gate_1_pass"]:
        print("GATE-1 FAILED: ffprobe build is not a conforming LGPL build.", file=sys.stderr)
        print(f"  violations: {audit['violations']}", file=sys.stderr)
        return 3

    samples = sorted(p for p in args.samples.glob("**/*") if p.is_file())
    if not samples:
        print(f"No samples found under {args.samples}", file=sys.stderr)
        return 4

    results = {
        "ffprobe_audit": audit,
        "mediainfo_sha256": _sha256(mediainfo),
        "required_fields": list(REQUIRED_FIELDS),
        "samples": {
            sample.name: {
                "sha256": _sha256(sample),
                "size": sample.stat().st_size,
                "ffprobe": probe_with_ffprobe(ffprobe, sample),
                "mediainfo": probe_with_mediainfo(mediainfo, sample),
            }
            for sample in samples
        },
    }

    args.out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {args.out} ({len(samples)} samples)")
    print(f"GATE-1: ffprobe build audit PASSED — licence {audit['licence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
