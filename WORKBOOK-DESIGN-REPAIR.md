# v0.0.0.1 — proposed repaired schema and audit traceability

Status: **draft / not owner-accepted**. This resolves the design choices at proposal level, not actual Excel qualification. The immutable original 28 findings remain open pending re-audit and workbook evidence. The common draft contract is [schemas/workbook-draft-v1.json](schemas/workbook-draft-v1.json). No spreadsheet or provider data has been created.

## Design decisions

Exactly 12 sheets, with a navigation-only README and 11 rectangular tables. Three control tables are manifest, dictionary and taxonomy; eight research tables remain empty in the blank. Preserve exact legacy registry labels (VM, GPU notebook, Dev workspace, CI runner, Container, Serverless, Research, API only, Other) independently of the broader existing foundation taxonomy. All material claims have field-specific evidence. Resource profiles prevent mixing mutually exclusive hardware/region variants. Optional unknown scalar values remain blank, not false; conflicts and not-applicable states are explicitly recorded through evidence and field-state relationships, with explicit typed field-state rows. No formula is permitted in the draft; a future exact allowlist may permit trusted dashboard calculations. Use external derived CSV/JSON views for LLM discovery. No schema/data version coupling.

## Original audit mapping

| Finding | Proposed corrective design |
|---|---|
| AUD-001 | 12-sheet bounded layout; one rectangular table per non-README sheet. |
| AUD-002 | Organization/platform/service hierarchy and offer foreign key. |
| AUD-003 | UUID v4 namespace, immutable identities and global duplicate validation. |
| AUD-004 | Explicit primary and foreign keys; cross-partition validation required. |
| AUD-005 | Free class retained; funding, eligibility, expiration and renewal separate. |
| AUD-006 | Nine exact legacy categories plus orthogonal dimensions and original broader taxonomy. |
| AUD-007 | Typed null, false/zero, explicit resource state and claim provenance. |
| AUD-008 | One canonical owner per field; derived views are nonauthoritative. |
| AUD-009 | Independent assessment dimensions; no weighted security score. |
| AUD-010 | Mandatory fee states, overage, cap, paid conversion and E6 scenario criteria. |
| AUD-011 | Claim-specific source, field, dates, outcome, grade and scenario. |
| AUD-012 | Compatibility status separates tested, supported, theoretical and prohibited. |
| AUD-013 | Append-only history and accepted versions preserved. |
| AUD-014 | Manifest partitions with row/size thresholds, global IDs and external digest. |
| AUD-015 | No external workbook formulas or self-referential checksums. |
| AUD-016 | Manual and importer table-expansion tests retained as actual workbook gates. |
| AUD-017 | Count entity types separately and avoid mixed profile joins. |
| AUD-018 | Claim review deadlines and explicit stale policy. |
| AUD-019 | Literal storage, safe CSV and existing package preflight; actual workbook tests remain. |
| AUD-020 | External evidence treated as untrusted data; no automatic source execution. |
| AUD-021 | Public-safe fields, no credential or private link storage; review remains necessary. |
| AUD-022 | Source mapping preserves all 54 original IDs and dispositions; no import performed. |
| AUD-023 | Versioned draft contract; accepted migration must prove parity and preserve IDs. |
| AUD-024 | Independent schema/data identities and immutable acceptance binding. |
| AUD-025 | Only essential identity and classification required; optional unknown remains null. |
| AUD-026 | Offline workbook and machine-readable exports, no macros or mandatory external tools. |
| AUD-027 | Explicit physical units, bounds and period rules; distinguish GB and GiB. |
| AUD-028 | Existing synthetic foundation regressions plus draft-schema structural checks; actual 30 workbook tests pending. |

## Remaining gates

Draft schema structural tests are not the 30 actual template acceptance tests. Before workbook construction, re-audit the schema, review claim completeness, numeric unit mapping and formula/formatting policy, and obtain explicit implementation approval. Before populated edition, verify actual accepted schema and bytes, immutable owner/auditor receipts, independent runner evidence and real source snapshot. No licensing decision or production credentials are implied. All previous audit records remain intact.

## Synthetic record validation

The shared `scripts/draft_records.py` is a draft contract validator, not a workbook writer. It checks strict field names and types, UUID identities, hierarchy, foreign keys, profile ownership, resource units and ranges, expiry consistency, assessment dimension separation, evidence targets, field-state links, and a conservative zero-cost gate. It accepts in-memory synthetic records only in CI. It does not certify actual source evidence, workbook formatting, complete field-level provenance, or real migrations. A draft cannot authorize a release.
