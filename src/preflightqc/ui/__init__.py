"""Layer 6 UI — the only layer permitted to import Qt.

Everything below this package is Qt-free and headlessly testable, which is what makes
the GUI framework replaceable (ADR-001 section 7) and what an automated import-boundary
test enforces.

The UI owns no domain logic. It renders immutable view-model snapshots and emits
commands.
"""
