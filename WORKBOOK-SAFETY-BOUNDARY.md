# Workbook safety boundary — Orange and Green Team

This repair strengthens package inspection, CSV export and URL screening before actual workbook construction. It rejects Unicode-obscured executable CSV prefixes without changing canonical data, NUL bytes, active XML elements, automatic defined names, special ZIP member types, duplicate content mappings, missing override targets, special-use IP addresses and uppercase URL-scheme bypasses. Synthetic regression cases exercise these protections.

This is a conservative preflight, not approval of arbitrary Excel formulas, a complete Office parser, real data classification, or provider security. Real workbook verification still requires the approved sheet/table/column dictionary, exact formula allowlist, actual source evidence and independent review. No real .xlsx or research row is committed. No production trust roots or approvals are fabricated.

The active pre-build gate remains unchanged. A future schema revision must specify the precise worksheet structure, cell types and approved formula inventory, enforce blank data tables and verified filled-data parity, and add production qualification tests. The existing original audit and readiness findings remain separately tracked.
