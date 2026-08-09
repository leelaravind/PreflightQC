# test-assets/ — RESERVED, EMPTY BY DESIGN

**No media files exist yet, and none will ever be committed.**

## The rule

Media files are **generated**, not committed. Committed here is only:

```
test-assets/
├── corpus-manifest.json        the committed source of truth   (Phase 9)
└── README.md                   this file
```

Generated (and git-ignored):

```
test-assets/generated/          the actual media fixtures
```

`.gitignore` blocks `test-assets/generated/` and every common video extension under this
tree. A Phase 9 test asserts no media file is committed.

## Why

- The repository stays small.
- Every fixture's construction is explicit, reviewable, and reproducible.
- A fixture's *intent* is documented next to its recipe rather than lost in a binary.

## How it works (Phase 9)

```
corpus-manifest.json  ──►  tools/generate_corpus.py  ──►  test-assets/generated/
                      ──►  tools/verify_corpus.py    ──►  checksum verification
```

Each manifest entry records: id, purpose, target preset(s), the exact generation recipe,
the expected checksum, and the expected outcome.

Generation must be **byte-identical** across machines: fixed seeds, bitexact flags, and no
encoder version string or creation timestamp written into the container. A fixture that
cannot be made bitexact is pinned to a recorded encoder version, and that dependency is
documented.

## Development-only encoder

The corpus is generated using a **development-only** FFmpeg encoder on the developer's
machine.

It is **never bundled**, **never referenced by application code**, and **never committed**.

This does not contradict spec §20's prohibition on the *product* encoding video — it is
dev tooling — and it is explicitly **not** permission to ship an encoder.

## Coverage required

PASS · WARN · FAIL · UNKNOWN · corrupt · unsupported · batch-mixed · boundary.

**Boundary pairs are the core deliverable**: for every hard deterministic rule, one
just-inside fixture and one just-outside fixture. Coverage is machine-verified against the
shipped preset rule set — an uncovered `FAIL` rule fails the build.

See `docs/testing/TEST-STRATEGY-V1.md` §3 and
`docs/planning/IMPLEMENTATION-PLAN-V1.md` §10.
