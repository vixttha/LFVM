# Architecture audit 01

All 28 findings remain open pending design repair, re-audit and approval; no implementation exists. Severity is inherited from the preceding planning audit.

| ID | Severity | Finding / required repair |
|---|---|---|
| AUD-001 | Critical | Excessive worksheet fragmentation; consolidate related data |
| AUD-002 | Critical | Provider and offer identity conflicts; distinguish organizations/platforms/services/offers |
| AUD-003 | High | Finite identifier namespace; immutable global IDs |
| AUD-004 | Critical | No database-grade foreign keys; explicit integrity checks |
| AUD-005 | Critical | Overlapping free classes; separate funding, expiration and eligibility |
| AUD-006 | High | Overlapping compute categories; orthogonal dimensions |
| AUD-007 | Critical | Ambiguous missing values; explicit unknown/false/not applicable |
| AUD-008 | Critical | Duplicate authoritative metadata; canonical fields |
| AUD-009 | Critical | Misleading security scoring; independent dimensions |
| AUD-010 | Critical | Incomplete zero-cost qualification; all fees and overages |
| AUD-011 | Critical | Insufficient evidence relationships; claim-level links |
| AUD-012 | High | Unsupported software compatibility assumptions; test vs theory |
| AUD-013 | High | Historical values can be overwritten; preserve revisions |
| AUD-014 | Critical | Unresolved partition strategy; global IDs and rollover |
| AUD-015 | High | Cross-workbook formula fragility; no mandatory external links |
| AUD-016 | High | Table expansion varies by importer; test both routes |
| AUD-017 | High | Dashboard double counts; distinct entities |
| AUD-018 | High | No freshness policy; review dates |
| AUD-019 | Critical | Formula injection; literal text and safe exports |
| AUD-020 | Critical | LLM prompt injection; source content untrusted |
| AUD-021 | High | Sensitive data risk; prohibit secrets |
| AUD-022 | High | Incomplete migration; preserve 54 source records separately |
| AUD-023 | High | No schema compatibility contract; versioned migration |
| AUD-024 | High | Template/data version conflicts; independent revisions |
| AUD-025 | Medium | Excessive mandatory metadata; partial records |
| AUD-026 | Medium | Unnecessary dependencies; offline functionality |
| AUD-027 | High | Inconsistent units; normalized values and periods |
| AUD-028 | High | No formal acceptance fixture; disposable synthetic data |

This is a design audit only; no claim of repaired findings or independently executed tests.
