# Version comparison

Predecessor: none (first blank version). Actual measured improvement/degradation: not applicable until a workbook exists.

## Proposal changes compared with original plan
- 20 worksheets reduced to 12 proposed sheets; fewer navigation steps expected, not measured.
- Added orthogonal classification dimensions, explicit missing values, claim evidence, partition integrity and import safety.
- Removed proposed weighted overall trust score in favor of independent risk and evidence dimensions.

## Potential regressions / tradeoffs
- Consolidation may produce wide tables, harder manual entry and mixed record types.
- Derived discovery fields require refresh discipline and tests against stale values.
- Normalized IDs and relationships add entry complexity; Excel does not enforce relational integrity.
- Independent risk grades reduce convenience of one-number sorting but avoid false confidence.

Actual regressions: unknown; no workbook or predecessor to compare. Do not substitute proposed improvements for measured outcomes. Future versions must document additions/removals, measured improvements, measured degradations, tradeoffs, unchanged features and exact evidence.
