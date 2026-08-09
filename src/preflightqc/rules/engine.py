"""The rule evaluation engine.

Pure: `(media, preset) -> findings`. No I/O, no clock, no locale, no randomness, so the
same inputs always produce byte-identical output on any machine (spec 11.3.1).

The engine contains no platform name and no platform threshold. It knows operators and
the metadata model; it knows nothing about Instagram, TikTok, YouTube, or LinkedIn
(spec 11.3.2).

Evaluation order, per ARCHITECTURE-V1.md section 6.3:

    1. guard false                -> SKIP, no finding
    2. property absent            -> UNKNOWN finding, never FAIL
    3. property conflicted        -> evaluate permissively, cap severity at WARN
    4. operator applies           -> pass or fail at the rule's (capped) severity
"""

from __future__ import annotations

from typing import Any

from preflightqc.core.model import PROPERTY_PATHS, NormalisedMedia
from preflightqc.core.values import MetaField, absent_reason
from preflightqc.rules import operators
from preflightqc.rules.document import Guard, PresetDocument, RuleRecord
from preflightqc.rules.finding import Finding, SourceReference, unknown_finding
from preflightqc.rules.severity import Classification, Severity, cap

#: The source cited by findings that report PreflightQC's own documented behaviour
#: rather than a platform requirement. Keeping these traceable too means every line in a
#: report can be justified, and it prevents a diagnostic being mistaken for a platform
#: claim.
SELF_SOURCE = SourceReference(
    source_ref="PREFLIGHTQC",
    title="PreflightQC V1 Specification",
    url="docs/specification/PREFLIGHTQC-V1-SPEC.md",
    access_date="2026-08-09",
    confidence="HIGH",
)


def _describe_expected(rule: RuleRecord) -> str:
    """Phrase the expected value as required or recommended, matching classification.

    This is not cosmetic. A WARN finding whose text reads like a rejection defeats the
    purpose of the severity model (spec 15).
    """
    operator = operators.get(rule.operator)
    body = operator.describe(rule.expected)
    unit = PROPERTY_PATHS[rule.property_path].unit
    if unit and operator.shape.value in ("scalar", "range"):
        body = f"{body} {unit}"
    if rule.classification in (Classification.HARD_REQUIREMENT, Classification.DOCUMENTED_LIMIT):
        return f"required: {body}"
    if rule.classification is Classification.ELIGIBILITY:
        return f"for eligibility: {body}"
    if rule.classification is Classification.UNKNOWN:
        return body
    return f"recommended: {body}"


def _describe_detected(field: MetaField[Any], rule: RuleRecord) -> str:
    unit = PROPERTY_PATHS[rule.property_path].unit
    text = field.describe()
    if field.is_known and unit:
        return f"{text} {unit}"
    return text


def _comparable(value: Any) -> Any:
    """Reduce a stored value to something the operators can compare.

    Fractions become floats here (and only here), which is why the model can afford to
    keep frame rates exact everywhere else.
    """
    from fractions import Fraction

    if isinstance(value, Fraction):
        return float(value)
    return value


def _evaluate_guard(media: NormalisedMedia, guard: Guard) -> bool:
    """A guard is satisfied only when it positively evaluates true.

    An absent or conflicted guard property yields False -- we cannot confirm the rule
    applies, so we do not apply it. Skipping is always safe; applying on an unconfirmed
    guard is not.
    """
    field = PROPERTY_PATHS[guard.property_path].resolve(media)
    if not field.is_known:
        return False
    operator = operators.get(guard.operator)
    try:
        return operator.apply(
            _comparable(field.value), guard.expected, guard.tolerance, guard.relative_tolerance
        )
    except operators.OperatorError:
        return False


def _apply(rule: RuleRecord, value: Any) -> bool | None:
    """Apply the rule's operator, or None when the comparison is not possible."""
    operator = operators.get(rule.operator)
    try:
        return operator.apply(_comparable(value), rule.expected, rule.tolerance, rule.relative_tolerance)
    except operators.OperatorError:
        return None


def evaluate_rule(media: NormalisedMedia, rule: RuleRecord) -> Finding | None:
    """Evaluate one rule. Returns None when the rule was skipped by a guard."""
    descriptor = PROPERTY_PATHS[rule.property_path]

    if any(not _evaluate_guard(media, guard) for guard in rule.guards):
        return None

    field = descriptor.resolve(media)
    expected_text = _describe_expected(rule)
    provenance = field.provenance.describe() if field.provenance else None

    # A rule whose classification is UNKNOWN is a documented gap: the source publishes
    # nothing, or the property is not measurable in V1. It reports, it never judges.
    if rule.classification is Classification.UNKNOWN:
        return unknown_finding(
            rule_id=rule.rule_id,
            classification=rule.classification,
            property_path=rule.property_path,
            property_label=descriptor.label,
            detected=_describe_detected(field, rule),
            expected=expected_text,
            explanation=rule.explanation,
            source=rule.source,
            reason=rule.note or "no authoritative specification is published for this property",
            provenance=provenance,
            unit=descriptor.unit,
        )

    # Specification 7.1: unavailable metadata is never a failure.
    if field.is_absent:
        return unknown_finding(
            rule_id=rule.rule_id,
            classification=rule.classification,
            property_path=rule.property_path,
            property_label=descriptor.label,
            detected=field.describe(),
            expected=expected_text,
            explanation=rule.explanation,
            source=rule.source,
            reason=absent_reason(field),
            provenance=provenance,
            unit=descriptor.unit,
        )

    if field.is_conflicted:
        return _evaluate_conflicted(field, rule, descriptor.label, expected_text)

    outcome = _apply(rule, field.value)
    if outcome is None:
        return unknown_finding(
            rule_id=rule.rule_id,
            classification=rule.classification,
            property_path=rule.property_path,
            property_label=descriptor.label,
            detected=_describe_detected(field, rule),
            expected=expected_text,
            explanation=rule.explanation,
            source=rule.source,
            reason="the detected value could not be compared against the expected value",
            provenance=provenance,
            unit=descriptor.unit,
        )

    return _finalise(
        rule,
        passed=outcome,
        detected=_describe_detected(field, rule),
        expected=expected_text,
        label=descriptor.label,
        unit=descriptor.unit,
        provenance=provenance,
    )


def _evaluate_conflicted(
    field: MetaField[Any],
    rule: RuleRecord,
    label: str,
    expected_text: str,
) -> Finding:
    """Evaluate a rule whose property the two inspectors disagreed about.

    The rule is evaluated against *every* competing value and passes if any of them
    passes -- the permissive reading. If it still fails, severity is capped at WARN,
    because we are not confident enough about what the file actually contains to reject
    it (spec 10.4).
    """
    outcomes = [_apply(rule, value) for value in field.conflict_values()]
    detected = field.describe()
    provenance = "inspectors disagree: " + ", ".join(
        p.describe() for _, p in field.conflict
    )

    if any(outcome is True for outcome in outcomes):
        return _finalise(
            rule,
            passed=True,
            detected=detected,
            expected=expected_text,
            label=label,
            unit=PROPERTY_PATHS[rule.property_path].unit,
            provenance=provenance,
            extra_note="The inspectors disagree about this value; the reading that satisfies the rule was used.",
        )

    finding = _finalise(
        rule,
        passed=False,
        detected=detected,
        expected=expected_text,
        label=label,
        unit=PROPERTY_PATHS[rule.property_path].unit,
        provenance=provenance,
        extra_note="The inspectors disagree about this value, so this cannot be reported as a failure.",
    )
    capped = cap(rule.classification, Severity.WARN)
    if finding.severity is Severity.FAIL:
        return Finding(
            rule_id=finding.rule_id,
            severity=capped,
            classification=finding.classification,
            property_path=finding.property_path,
            property_label=finding.property_label,
            detected=finding.detected,
            expected=finding.expected,
            explanation=finding.explanation,
            source=finding.source,
            provenance=finding.provenance,
            unit=finding.unit,
            passed=False,
            unknown_reason=finding.unknown_reason,
        )
    return finding


def _finalise(
    rule: RuleRecord,
    *,
    passed: bool,
    detected: str,
    expected: str,
    label: str,
    unit: str | None,
    provenance: str | None,
    extra_note: str | None = None,
) -> Finding:
    """Build the finding for a rule that was actually evaluated.

    A passing rule reports at INFO, never at its own severity -- otherwise a satisfied
    FAIL-class rule would itself read as a failure.
    """
    explanation = rule.explanation
    if passed and rule.message_pass:
        explanation = rule.message_pass
    elif not passed and rule.message_fail:
        explanation = rule.message_fail
    for note in (rule.note, extra_note):
        if note:
            explanation = f"{explanation} {note}"

    severity = Severity.INFO if passed else cap(rule.classification, rule.severity)
    return Finding(
        rule_id=rule.rule_id,
        severity=severity,
        classification=rule.classification,
        property_path=rule.property_path,
        property_label=label,
        detected=detected,
        expected=expected,
        explanation=explanation,
        source=rule.source,
        provenance=provenance,
        unit=unit,
        passed=passed,
    )


def _diagnostic_findings(media: NormalisedMedia) -> list[Finding]:
    """INFO findings for PreflightQC's own documented behaviour (spec 23)."""
    findings: list[Finding] = []
    for index, note in enumerate(media.diagnostics.notes):
        findings.append(
            Finding(
                rule_id=f"preflightqc.diagnostic.{index:02d}",
                severity=Severity.INFO,
                classification=Classification.UNKNOWN,
                property_path="container.stream_count",
                property_label="Stream inventory",
                detected=note,
                expected="informational",
                explanation=note,
                source=SELF_SOURCE,
                passed=False,
            )
        )
    for index, conflict in enumerate(media.diagnostics.conflicts):
        detail = (
            f"{conflict.property_path}: "
            + " vs ".join(f"{v} [{i}]" for v, i in zip(conflict.values, conflict.inspectors, strict=False))
        )
        findings.append(
            Finding(
                rule_id=f"preflightqc.conflict.{index:02d}",
                severity=Severity.INFO,
                classification=Classification.UNKNOWN,
                property_path=conflict.property_path,
                property_label="Inspector disagreement",
                detected=detail,
                expected="informational",
                explanation=(
                    "The two inspectors reported different values for this property. "
                    "Both are shown; PreflightQC does not silently choose between them."
                ),
                source=SELF_SOURCE,
                passed=False,
            )
        )
    return findings


def evaluate(media: NormalisedMedia, preset: PresetDocument) -> tuple[Finding, ...]:
    """Evaluate every enabled rule in the preset against the media.

    Findings are returned in the deterministic display order defined by spec 15:
    FAIL, WARN, UNKNOWN, INFO; within a severity, by rule id.
    """
    findings = [
        finding
        for rule in preset.enabled_rules
        if (finding := evaluate_rule(media, rule)) is not None
    ]
    findings.extend(_diagnostic_findings(media))
    findings.sort(key=lambda f: f.sort_key())
    return tuple(findings)
