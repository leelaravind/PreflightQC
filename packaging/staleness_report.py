"""Preset source staleness report (Phase 12 deliverable 6).

Platform delivery specifications change without notice and without a changelog. A rule
whose source has not been looked at in six months is not necessarily wrong — but nobody
can say it is right, and the product's whole claim is that every finding traces to a
first-party source that someone actually read.

So this reports **age**, not correctness. It cannot tell you TikTok changed its maximum
duration; it can tell you that nobody has checked since February, which is the fact a
release decision actually turns on.

Register rule 6: *"Every row carries the access date of its source. Rules whose sources
have not been re-verified within 6 months are flagged stale at the release gate."*

    python packaging/staleness_report.py
    python packaging/staleness_report.py --as-of 2027-01-01     # what will be stale then
    python packaging/staleness_report.py --max-age-days 90
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRESETS = REPO_ROOT / "presets"

#: Six months, as the register states it. Not a rolling calendar month calculation:
#: an off-by-a-day threshold is not what this is protecting against.
DEFAULT_MAX_AGE_DAYS = 183


@dataclass(frozen=True, slots=True)
class RuleAge:
    preset_id: str
    rule_id: str
    source_ref: str
    verified: date
    age_days: int

    @property
    def line(self) -> str:
        return (
            f"{self.preset_id:32} {self.rule_id:44} {self.source_ref:8} "
            f"{self.verified.isoformat()}  {self.age_days:5d}d"
        )


@dataclass
class Report:
    as_of: date
    max_age_days: int
    total_rules: int = 0
    total_presets: int = 0
    stale: list[RuleAge] = None  # type: ignore[assignment]
    integrity_problems: list[str] = None  # type: ignore[assignment]
    oldest: RuleAge | None = None

    def __post_init__(self) -> None:
        if self.stale is None:
            self.stale = []
        if self.integrity_problems is None:
            self.integrity_problems = []


def _parse(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def analyse(
    presets_dir: Path, *, as_of: date, max_age_days: int = DEFAULT_MAX_AGE_DAYS
) -> Report:
    report = Report(as_of=as_of, max_age_days=max_age_days)

    for path in sorted(presets_dir.rglob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        preset_id = str(document.get("preset_id", path.stem))
        report.total_presets += 1

        sources = {
            str(entry.get("source_ref")): _parse(str(entry.get("access_date", "")))
            for entry in document.get("sources", [])
        }
        if not sources:
            report.integrity_problems.append(f"{preset_id}: declares no sources")

        for rule in document.get("rules", []):
            report.total_rules += 1
            rule_id = str(rule.get("rule_id", "<unnamed>"))
            source_ref = str(rule.get("source_ref", ""))

            if source_ref and source_ref not in sources:
                report.integrity_problems.append(
                    f"{preset_id}: rule {rule_id} cites {source_ref}, which the preset "
                    "does not declare — the finding cannot be traced to a source"
                )

            rule_date = _parse(str(rule.get("last_verified_date", "")))
            source_date = sources.get(source_ref)
            candidates = [d for d in (rule_date, source_date) if d is not None]
            if not candidates:
                report.integrity_problems.append(
                    f"{preset_id}: rule {rule_id} has no usable verification date"
                )
                continue

            # The older of the two governs. A rule re-dated without re-reading its
            # source would otherwise look fresh purely because someone touched the file.
            verified = min(candidates)
            age = (as_of - verified).days
            entry = RuleAge(preset_id, rule_id, source_ref or "-", verified, age)
            if report.oldest is None or age > report.oldest.age_days:
                report.oldest = entry
            if age > max_age_days:
                report.stale.append(entry)

    report.stale.sort(key=lambda item: -item.age_days)
    return report


def render(report: Report) -> str:
    lines = [
        "PREFLIGHTQC — PRESET SOURCE STALENESS REPORT",
        "=" * 78,
        f"As of        : {report.as_of.isoformat()}",
        f"Threshold    : {report.max_age_days} days (register rule 6: 6 months)",
        f"Presets      : {report.total_presets}",
        f"Rules        : {report.total_rules}",
        "",
    ]
    if report.oldest is not None:
        lines.append(
            f"Oldest rule  : {report.oldest.rule_id} — verified "
            f"{report.oldest.verified.isoformat()} ({report.oldest.age_days} days ago)"
        )
        lines.append("")

    if report.integrity_problems:
        lines.append(f"TRACEABILITY PROBLEMS ({len(report.integrity_problems)})")
        lines.append("-" * 78)
        lines.extend(f"  {problem}" for problem in report.integrity_problems)
        lines.append("")

    if report.stale:
        lines.append(f"STALE RULES ({len(report.stale)})")
        lines.append("-" * 78)
        lines.extend(f"  {item.line}" for item in report.stale)
        lines.append("")
        lines.append(
            "Each of these must be re-checked against its first-party source before "
            "release. Re-dating a rule without re-reading the source is not a fix."
        )
    else:
        lines.append("No stale rules. Every rule's source was verified within the threshold.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preset source staleness report")
    parser.add_argument("--presets", type=Path, default=PRESETS)
    parser.add_argument("--as-of", type=str, default=None, help="YYYY-MM-DD, default today")
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    as_of = _parse(args.as_of) if args.as_of else date.today()
    if as_of is None:
        print(f"error: --as-of must be YYYY-MM-DD, got {args.as_of!r}", file=sys.stderr)
        return 2

    report = analyse(args.presets, as_of=as_of, max_age_days=args.max_age_days)
    text = render(report)
    print(text)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"Written to {args.out}")

    if report.integrity_problems:
        return 1
    return 1 if report.stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
