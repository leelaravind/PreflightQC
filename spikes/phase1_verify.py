"""Phase 1 verification: real binaries, real media, the shipping pipeline.

Drives ffprobe + MediaInfo -> normalise -> the real `NormalisedMedia` model, and reports
a determinability verdict for every field the specification requires (spec section 9).

This is the deliverable GATE-1 turns on. It is deliberately *observational*: it records
what the inspectors actually report and never asserts what they ought to report. Missing
values stay UNKNOWN.

    python spikes/phase1_verify.py --samples DIR [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from preflightqc.adapters import ffprobe as ffprobe_adapter
from preflightqc.adapters import mediainfo as mediainfo_adapter
from preflightqc.core.model import PROPERTY_PATHS
from preflightqc.core.values import FieldState
from preflightqc.normalise.normaliser import normalise
from preflightqc.platform import binaries

REPO_ROOT = Path(__file__).resolve().parent.parent


def inspect_one(path: Path, ff_path: Path, mi_path: Path, timeout: float) -> dict[str, Any]:
    """Run both real inspectors over one file and normalise the result."""
    ff_outcome = ffprobe_adapter.inspect(ff_path, path, timeout_seconds=timeout)
    mi_outcome = mediainfo_adapter.inspect(mi_path, path, timeout_seconds=timeout)

    record: dict[str, Any] = {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "ffprobe_ok": ff_outcome.ok,
        "mediainfo_ok": mi_outcome.ok,
    }
    if not ff_outcome.ok:
        record["ffprobe_failure"] = {
            "kind": ff_outcome.kind.value,  # type: ignore[union-attr]
            "message": ff_outcome.message,  # type: ignore[union-attr]
        }
    if not mi_outcome.ok:
        record["mediainfo_failure"] = {
            "kind": mi_outcome.kind.value,  # type: ignore[union-attr]
            "message": mi_outcome.message,  # type: ignore[union-attr]
        }

    if not ff_outcome.ok and not mi_outcome.ok:
        record["normalised"] = None
        record["verdict"] = "NOT_INSPECTED"
        return record

    media = normalise(
        path,
        ffprobe=ffprobe_adapter.parse_outcome(ff_outcome),
        mediainfo=mediainfo_adapter.parse_outcome(mi_outcome),
        size_bytes=path.stat().st_size,
    )

    fields: dict[str, Any] = {}
    for prop, descriptor in PROPERTY_PATHS.items():
        field = descriptor.resolve(media)
        entry: dict[str, Any] = {"state": field.state.value, "display": field.describe()}
        if field.provenance is not None:
            entry["from"] = field.provenance.describe()
        if field.state is FieldState.CONFLICTED:
            entry["values"] = [str(v) for v in field.conflict_values()]
        if field.reason:
            entry["reason"] = field.reason
        fields[prop] = entry

    record["normalised"] = fields
    record["conflicts"] = [
        {"property": c.property_path, "values": list(c.values), "inspectors": list(c.inspectors)}
        for c in media.diagnostics.conflicts
    ]
    record["notes"] = list(media.diagnostics.notes)
    record["verdict"] = "INSPECTED"
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 real-binary verification")
    parser.add_argument("--samples", type=Path, default=REPO_ROOT / "spikes" / "samples")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "spikes" / "phase1-findings.json")
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    startup = binaries.check_all()
    ff = startup.get(binaries.InspectorKind.FFPROBE)
    mi = startup.get(binaries.InspectorKind.MEDIAINFO)
    if ff is None or mi is None or not ff.available or not mi.available:
        print("Phase 1 requires both inspectors.", file=sys.stderr)
        return 2
    if not ff.licence_ok:
        print(f"ffprobe build is not acceptable: {ff.licence_violations}", file=sys.stderr)
        return 3
    assert ff.path is not None and mi.path is not None

    samples = sorted(p for p in args.samples.glob("*") if p.is_file())
    if not samples:
        print(f"No samples under {args.samples}", file=sys.stderr)
        return 4

    results = [inspect_one(p, ff.path, mi.path, args.timeout) for p in samples]

    # Determinability matrix: for each required field, how often was it actually known?
    matrix: dict[str, dict[str, int]] = {}
    for prop in PROPERTY_PATHS:
        counter: Counter[str] = Counter()
        for r in results:
            if r["normalised"] is None:
                continue
            counter[r["normalised"][prop]["state"]] += 1
        matrix[prop] = dict(counter)

    payload = {
        "inspectors": {
            "ffprobe": {"version": ff.version, "licence": ff.licence, "path": str(ff.path)},
            "mediainfo": {"version": mi.version, "licence": mi.licence, "path": str(mi.path)},
        },
        "ffprobe_configuration": ff.configuration,
        "sample_count": len(samples),
        "determinability_matrix": matrix,
        "files": results,
    }
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    inspected = sum(1 for r in results if r["verdict"] == "INSPECTED")
    print(f"ffprobe   {ff.version}  ({ff.licence})")
    print(f"mediainfo {mi.version}  ({mi.licence})")
    print(f"samples: {len(samples)}   inspected: {inspected}   not inspected: {len(samples) - inspected}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
