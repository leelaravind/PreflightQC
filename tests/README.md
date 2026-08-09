# tests/ — RESERVED, EMPTY BY DESIGN

**No tests exist yet. This is correct.** The project is in the planning phase.

Full strategy: `docs/testing/TEST-STRATEGY-V1.md`.

## Planned layout

```
tests/
├── conftest.py
├── docs/                  documentation invariants                    (Phase 0)
├── core/                  three-valued types, vocabulary, geometry    (Phase 2)
├── normalise/             normaliser, conflict preservation           (Phase 2)
├── rules/                 severity guard, loader, operators, engine   (Phase 3)
├── results/               overall-status truth table                  (Phase 3)
├── presets/               shipped preset data assertions              (Phase 4)
├── platform/              process runner                              (Phase 5)
├── adapters/              inspector adapters (stub executables)       (Phase 5)
├── scan/                  enumeration                                 (Phase 5)
├── orchestration/         isolation, cancellation, cache              (Phase 5)
├── ui/                    capability tests (pytest-qt)                (Phase 6)
├── profiles/              custom profile compile/store/roundtrip      (Phase 7)
├── reporting/             contents, self-containment, snapshots       (Phase 8)
├── golden/                the golden corpus suite                     (Phase 9)
├── integration/           spec §23 failure matrix, soak, end-to-end   (Phase 10)
├── safety/                network, file-mutation, PATH, orphans       (Phases 5, 8)
└── architecture/          import boundaries, platform-data scans      (Phase 2+)
```

## The four claims these tests defend

| # | Claim |
| --- | --- |
| **C1** | A recommendation **never** produces `FAIL`. |
| **C2** | Missing or undeterminable metadata **never** produces `FAIL`. |
| **C3** | Rule values match their sources **exactly**. |
| **C4** | One broken file **never** terminates a batch, and source files are **never** modified. |

**A test that does not defend one of these, or a stated acceptance criterion, should not
be written.**

## The most important file

`tests/rules/test_severity_guard.py`. The severity invariant is the product; that file is
where it is proven.
