# Filled spreadsheet development workflow

| Stage | Role | Exit evidence |
|---|---|---|
| Plan | Head | Data version, scope, predecessor, target template, source inventory |
| Audit | Internal Auditor | Source quality and schema readiness findings |
| Approve | Owner | Explicit import/build scope approval |
| Import / update | Worker | Exact accepted blank copy, public-safe source snapshot, typed records and mappings |
| Validate | Validator | Exact candidate, integrity/coverage/safety tests and runner receipts |
| Audit | Internal Auditor | Reconciliation, source confidence, regressions and unresolved issues; disclose independence |
| Qualify | Head | Exact candidate artifact digest, comparison and evidence |
| Lock | Owner | Exact candidate acceptance; immutable archive and index update |

States: blocked_on_template, planned, approved, implementing, validating, review_pending, qualified, locked, superseded, rejected. Only one active version; failed checks return to Worker without unauthorized scope expansion. A green metadata check is not workbook qualification. Preserve prior editions even if source facts change.

For the initial 54 source records, capture a public-safe immutable input snapshot and digest, preserve every source record ID with a mapping to normalized IDs or explicit disposition, and reconcile counts. Do not infer that all source records are current or free. Reverify material claims when stale; unknown or contradictory values stay explicit. Subsequent releases record added/changed/removed-from-current/expired/corrected offers, provider deduplication, evidence changes and risk reclassifications, never silently erase history.

Version lock requires exact template binding, owner approval, artifact inventory and SHA-256 digests, reconciled source counts, completed tests, exact commit/runner evidence and comparison. Record commit hash in an external or subsequent receipt to avoid self-referential hashes. No real account signups, private data access or payment tests without specific authorization.

## Current implementation boundary
The state model above describes the intended future lifecycle. The executable [foundation gate](FOUNDATION-GATE.md) currently admits only pre-build states. A successor contract and verified release mechanism are necessary before advancing. Metadata CI is never workbook qualification or owner approval.
