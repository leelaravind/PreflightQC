# src/ — RESERVED, EMPTY BY DESIGN

**No application code exists yet. This is correct.**

The project is in the planning phase. Implementation begins only when
`docs/planning/IMPLEMENTATION-PLAN-V1.md` is explicitly approved for execution.

## Planned layout

Populated by the implementation plan's phases, in this order:

```
src/preflightqc/
├── __init__.py            __version__ — single source of truth        (Phase 0)
├── platform/              L0 — process runner, paths, binaries        (Phase 5)
├── adapters/              L1 — ffprobe and MediaInfo adapters         (Phases 2, 5)
├── core/                  L2 — values, model, vocabulary, geometry    (Phase 2)
├── normalise/             L2 — precedence table, normaliser           (Phase 2)
├── rules/                 L3 — schema, loader, operators, engine      (Phase 3)
├── results/               L3 — aggregation                            (Phase 3)
├── scan/                  L5 — enumeration                            (Phase 5)
├── orchestration/         L5 — jobs, batch, runner, cache             (Phase 5)
├── reporting/             L4 — model, CSV, HTML                       (Phase 8)
├── profiles/              custom client profiles                      (Phase 7)
├── ui/                    L6 — the ONLY layer permitted to import Qt  (Phase 6)
└── cli/                   dev-only headless entry point               (Phase 5)
```

`presets/` (preset data) lives at the repository root, not under `src/`, because it is
data shipped alongside the application rather than importable code.

## The one rule to remember

**No module below `ui/` may import Qt, and dependencies point downward only.**

This is enforced by `tests/architecture/test_import_boundaries.py` from Phase 2 onward.
It is what keeps the engine headlessly testable and what makes the ADR-001 GUI-framework
fallback affordable.

See `docs/architecture/ARCHITECTURE-V1.md` §1 for the full layer contract.
