# Template version workflow

Canonical procedure; read AGENTS.md and TEMPLATE-LAWS.md first.

| Stage | Owner/role | Exit evidence |
|---|---|---|
| Plan | Head | Scope, predecessor, schema, known issues, tests |
| Audit plan | Internal Auditor | Findings, severity, proposed repairs; disclose reviewer independence |
| Authorize | Owner | Explicit scope approval |
| Implement | Worker | Blank XLSX, schema, dictionary, taxonomy, reproducible changes |
| Validate | Validator | Exact candidate, standard public runner logs, structural/data/safety/scale/portability tests |
| Audit candidate | Internal Auditor | Independent findings or explicitly labeled self-audit; regressions and limits |
| Acceptance | Head -> Owner | Exact revision and artifact SHA-256, differences, improvements, regressions, unresolved risks |
| Lock | Owner | Explicit acceptance; archive immutable version, update index |

Use one active version. States: planned, audit_pending, approved, implementing, validating, review_pending, qualified, locked, superseded, rejected. A passed test is not owner acceptance. Failure returns to Worker under unchanged approved scope; scope changes require approval. A qualified but unlocked version is not an accepted release.

For every version, use the archive directory rules. Compare to the previous locked version, or state no predecessor. Quantify improvements and degradations where measured, otherwise mark untested or unknown. Do not hide tradeoffs. Preserve negative results.

Evidence: exact commit SHA (record externally or in a later receipt to avoid a self-referential hash), workflow run/job URL, artifact path/digest, test counts, environment, reviewer, date and limitations. Never mark a gate complete based solely on a green unrelated run.

Current setup validation is documentation-only; workbook tests remain pending until a candidate exists.

## Current implementation boundary
The state model above describes the intended future lifecycle. The executable [foundation gate](FOUNDATION-GATE.md) currently admits only pre-build states. A successor contract and verified release mechanism are necessary before advancing. Metadata CI is never workbook qualification or owner approval.
