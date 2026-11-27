# Foundation gate — mission LFVM-FOUNDATION-AUDIT-001

This gate is the current executable **pre-build** contract, shared byte-for-byte by the template producer and research consumer. Read the original [Orange Team handoff](ORANGE-TEAM-HANDOFF.md). The user authorized non-destructive foundation repair and retesting, not workbook creation, research import, release, main integration or self-approval.

## Enforced now

- Strict bounded UTF-8 JSON, duplicate-key rejection, exact keys and scalar types; explicit errors under normal and optimized Python.
- Branch and version namespace, initial version, single active checkpoint, valid current state, document inventory, exact source baseline and test totals. No release, artifact, approval flag, import, or fake qualification can pass this pre-build validator.
- Current archive rejects extra entries recursively by directory allowlist, case-insensitive aliases, links/reparse points and invalid file types. CI checks tracked paths, no spreadsheet file anywhere, original audit-handoff bytes and baseline ancestry.
- Shared taxonomy and receipt contract in [foundation-contract.json](schemas/foundation-contract.json). No automatic changes to existing research categories; 54 denotes input records, not unique providers. No external service is needed.
- Bounded package-only XLSX preflight and safe CSV text export helper with synthetic tests. These are **not** a full workbook-content validator, schema parity verifier or public-data scanner.
- CI runs on standard public Ubuntu and Windows runners, push and PR targeting the dedicated branch, pinned checkout with read-only permissions and credential persistence disabled. Tests run under normal Python and python -O. PR runs are validation only, not exact release evidence. Manual dispatch is intentionally removed because the workflow is not on main.
- Original history and handoff preserved; no force push. Before any future writes read exact head, publish related files atomically, verify non-force revision, and re-read; on conflict stop and reconcile. Recovery uses a corrective successor commit, not a destructive reset.

## Fail-closed release boundary

Contract v1 supports only the current pre-build state. It intentionally does **not** accept even syntactically plausible release or dependency receipts. The first blank must have its 28 architecture findings resolved, actual schema approved, and a new release-gate contract implemented and qualified before moving beyond this gate. The filled edition must remain blocked until a genuinely owner-accepted blank exists. The current gate is not an owner authorization mechanism and cannot establish independent acceptance by itself. No approvals may be fabricated or written by the worker.

A future contract revision must establish a trusted external approval record (not editable flags or a candidate-generated receipt), exact approved scope, candidate commit, full qualification suite and actual artifact SHA-256; acceptance must reference those exact bytes. Verify identity/provenance from a trusted authority outside the candidate. Keep accepted receipts append-only and verify previously accepted bytes against that authority and ancestry; record supersession separately without changing locked manifests. A candidate can alter its own validator in an unprotected branch: do not claim protection from authorized repository writers or independent assurance based on self-tests.

Producer hands off immutable accepted template commit/path/digest, schema/dictionary/taxonomy fingerprints, receipt and test evidence. Consumer independently verifies upstream ancestry, bytes, acceptance and compatibility; no moving branch-head substitution. Bind data edition to that release. Reconcile each source record once (including duplicate, excluded or superseded dispositions) separately from normalized providers/offers. Verify actual sanitized snapshot bytes/digest, claim provenance, freshness, conflicting values, billing restrictions and public-safe publication. Partitions require canonical paths, global IDs, inventory, counts, digests and rollback/recovery tests. No data import, actual workbook or release can pass contract v1.

## Validation and trust

Run the branch-specific validator with --ci in GitHub Actions and the synthetic tests under both Python modes. CI success is a **foundation_metadata** receipt only; do not treat it as workbook qualification or owner approval. Verify job logs and exact commit independently. No branch protection or paid runner is required. No separate independent team runtime has been launched; subsequent Red/Blue/Purple reviews must distinguish source inspection, executable tests and deferred release gates. This is a conservative restriction, not proof of bulletproof security. Future contract evolution must preserve compatible identifiers and data, with explicit migration and negative tests.

## Independent-verifier support
Read [QUALIFICATION-PROTOCOL.md](QUALIFICATION-PROTOCOL.md). Shared signed-receipt, history, dependency, source and partition verification primitives are available for synthetic tests. The active gate remains pre-build only; no trusted production keys or independent retrieval adapter have been configured.
