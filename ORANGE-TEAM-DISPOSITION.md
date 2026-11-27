# Orange Team repair disposition — foundation candidate

Mission LFVM-FOUNDATION-AUDIT-001. All 45 original IDs remain traceable in ORANGE-TEAM-HANDOFF.md. This candidate addresses the pre-build foundations; no workbook, import, approval, release, or fake qualification is created. No original issue is marked verified merely because code was committed. Pending actual public runner retest.

| Findings | Disposition before runner confirmation | Implementation / residual |
|---|---|---|
| A01–A04, A18–A19, A22, A37–A38 | Repaired pending retest | Explicit strict validator, current lifecycle and pointer, JSON/type checks, archive inventory, test fixtures. |
| A05–A07, A09, A13–A17, A31, A39–A40 | Contained; release controls remain open | Pre-build denies progression, editable approvals, fabricated lock/test counts, artifact and template binding. Actual independently trusted receipts, locked history comparison, upstream qualification, reconciliation and schema parity require next approved contract. |
| A08, A20–A21 | Partially repaired | Version namespace/grammar, no successor before lock, shared machine contract and existing taxonomy; future predecessor/acceptance semantics still need release gate. |
| A10–A12, A28, A30, A44 | Partially repaired pending retest | Exact archive allowlist, path safety, bounded JSON and streaming hash, conservative package preflight and CSV helper; real XLSX/OOXML schema, formula allowlist, ingestion and external-link validation still require workbook implementation. |
| A15, A33–A34, A41, A45 | Deferred with explicit dependency | Source mapping, freshness, partition protocol, actual migration/recovery, artifact generation and qualification need approved schema and workbook. |
| A23, A25–A27, A36 | Repaired configuration pending runner evidence | Push/PR, Ubuntu/Windows, recorded environment, read-only checkout, identity and ancestry check; confirm actual jobs. |
| A24 | Repaired configuration pending retest | No reliance on branch-only manual dispatch. |
| A29 | Open | Public-safe data/secret scan not implemented; current gate prohibits any real data/artifacts. |
| A32, A42 | Partially repaired | Revision-safe publication/recovery instructions and branch-local handoff; future transition/partial-publication recovery needs executable release tests. |
| A35 | Deferred | Licensing policy not inferred; no license change or release. |
| A43 | Open separate workstream | 28 blank architecture findings and seven filled readiness findings preserved. |

The categories overlap when an issue has both current containment and a future gate (A15). No full-release readiness claim. Verify test results against the exact new head; use only standard free public GitHub runners. If status/log retrieval is unavailable, retain pending rather than mark passing.

## First runner results and corrective candidate

The first candidate passed 54 synthetic tests in each Python mode on Ubuntu in both branches. Windows failed the immutable-handoff check before running the tests because checkout converted line endings (runs 45921006671 and 45921008227). Repair compares the immutable Git blobs and permits only the canonical checkout line-ending transformation; adds three regression tests and explicit LF attributes for repository text. Checkout is pinned to upstream v7.0.1 (verified tag 3d3c42e5aac5ba805825da76410c181273ba90b1; Node 24) to address the runner's deprecated-runtime warning. Corrective exact-head results are pending. Preserve the original failed evidence.
