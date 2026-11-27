# Template laws

- Separate blank template schema versions from research library data revisions.
- Preserve existing F0–F5 free classes, A/B/C/U trust, access classes and compute taxonomy; use orthogonal eligibility, funding, expiration and environment fields.
- Stable globally unique immutable IDs, one record per row, atomic values, typed columns, ISO 8601 dates, documented numeric units, explicit unknown / false / not applicable.
- One authoritative field location; derived discovery fields must be reproducible and labeled. Provider, platform, service and offer identities must not be conflated.
- Explicit validated foreign keys and many-to-many relations; evidence at claim level, source date and review freshness. No deletion of expired or superseded records without preservation.
- No arbitrary trust score that confuses evidence coverage with actual safety. Billing, privacy, security and legitimacy are independent. $0 claims include mandatory fees, networking, storage, overage and renewal.
- Excel is finite (1,048,576 rows per sheet). Logical growth via registered partitions and global IDs; no required external workbook formulas.
- Macro-free XLSX; no external automatic connections, no credentials, no formula injection, safe export, untrusted source content is data. Offline and portable with CSV/JSON compatibility.
- Blank artifacts must contain no real research or test rows. Taxonomy and schema definitions are allowed. Maintain independent version and data identifiers.
- Explicit version comparisons: additions, removals, improvements, regressions, tradeoffs, unknowns and evidence. Never assert safety or improvement without support.
- Reproducible qualification using only standard free GitHub-hosted public runners. Owner retains authority over scope, lock and integration.
