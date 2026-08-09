"""Headless entry point.

Development and test tooling: it drives the same pipeline the UI does, without Qt, so
the golden corpus and the integration tests exercise the real path rather than a
parallel one.

    python -m preflightqc.cli.headless <paths...> --preset <id> [--json] [--report DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from preflightqc import __version__
from preflightqc.orchestration.runner import BatchRunner, InspectionSettings
from preflightqc.platform import binaries
from preflightqc.platform.paths import shipped_presets_dir, user_profiles_dir
from preflightqc.reporting import export as export_module
from preflightqc.reporting.export import ExportFormat
from preflightqc.reporting.model import build_report
from preflightqc.rules.loader import load_catalog
from preflightqc.scan.enumerate import EnumerationOptions, enumerate_inputs


def build_catalog():
    """Shipped presets first, so a custom profile can never shadow one."""
    shipped = load_catalog([shipped_presets_dir()])
    reserved = frozenset(p.preset_id for p in shipped.presets)
    custom = load_catalog([user_profiles_dir()], reserved_ids=reserved)
    return shipped, custom


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="preflightqc", description="Offline video QC")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--preset", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--no-recurse", action="store_true")
    parser.add_argument("--hdr-frame", action="store_true", help="read one frame for HDR side data")
    parser.add_argument("--json", action="store_true", help="emit machine-readable results")
    parser.add_argument("--report", type=Path, help="directory to write CSV and HTML reports into")
    args = parser.parse_args(argv)

    startup = binaries.check_all()
    if not startup.usable:
        for problem in startup.problems():
            print(f"error: {problem}", file=sys.stderr)
        return 2
    for problem in startup.problems():
        print(f"warning: {problem}", file=sys.stderr)

    shipped, custom = build_catalog()
    preset = shipped.by_id(args.preset) or custom.by_id(args.preset)
    if preset is None:
        available = sorted(p.preset_id for p in (*shipped.presets, *custom.presets))
        print(f"error: unknown preset '{args.preset}'. Available: {available}", file=sys.stderr)
        return 2

    enumerated = enumerate_inputs(
        args.paths, options=EnumerationOptions(recurse=not args.no_recurse)
    )
    if not enumerated.files:
        print("error: no files found", file=sys.stderr)
        return 2

    started = datetime.now().astimezone()
    runner = BatchRunner(
        startup=startup,
        settings=InspectionSettings(
            workers=args.workers,
            timeout_seconds=args.timeout,
            read_hdr_frame=args.hdr_frame,
        ),
    )
    outcome = runner.run(enumerated.files, preset)
    finished = datetime.now().astimezone()

    report = build_report(
        results=outcome.results,
        summary=outcome.summary,
        preset=preset,
        product_version=__version__,
        scan_started=started,
        scan_finished=finished,
        inspector_versions=startup.versions(),
    )

    if args.json:
        print(
            json.dumps(
                {
                    "preset": preset.preset_id,
                    "ruleset_version": preset.ruleset_version,
                    "summary": report.status_counts,
                    "files": [
                        {
                            "name": f.name,
                            "status": f.status,
                            "counts": dict(f.counts),
                            "findings": [
                                {
                                    "rule_id": x.rule_id,
                                    "severity": x.severity,
                                    "detected": x.detected,
                                    "expected": x.expected,
                                }
                                for x in f.actionable
                            ],
                        }
                        for f in report.files
                    ],
                },
                indent=2,
            )
        )
    else:
        for file in report.files:
            print(f"{file.status:>14}  {file.name}")
            for finding in file.actionable:
                print(f"                {finding.severity:<8} {finding.property_label}: {finding.detected}")
        print()
        for status, count in report.status_counts.items():
            if count:
                print(f"{status}: {count}")

    if args.report:
        for fmt in (ExportFormat.CSV, ExportFormat.HTML):
            destination = args.report / export_module.suggested_filename(report, fmt)
            result = export_module.export(report, destination, fmt)
            if result.ok:
                print(f"wrote {', '.join(str(p) for p in result.written)}", file=sys.stderr)
            else:
                print(f"error: {result.error}", file=sys.stderr)
                return 1

    return 1 if report.status_counts.get("FAIL", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
