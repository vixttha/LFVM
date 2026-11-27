# Orange Team retest and disposition — LFVM-FOUNDATION-AUDIT-001

Scope: permanent template and research-library branches only. This is a foundation-metadata retest, not a release or workbook qualification. No independent team runtime or independent owner/auditor production credentials were used. The original 45-ID handoff is preserved. Previous repair commits were present before this retest and retained.

## Exact code evidence

| Branch | Tested commit | Public runner evidence |
|---|---|---|
| template | `9a58d655d38f6fa83dca25632785d492895647bf` | [run 45921816480](https://github.com/vixttha/LFVM/actions/runs/45921816480) · [Ubuntu](https://github.com/vixttha/LFVM/actions/runs/45921816480/job/140254062847) · [Windows](https://github.com/vixttha/LFVM/actions/runs/45921816480/job/140254063090) |
| library | `a2157a92f40ba5397611c6d19a7ad768730e4502` | [run 45921818915](https://github.com/vixttha/LFVM/actions/runs/45921818915) · [Ubuntu](https://github.com/vixttha/LFVM/actions/runs/45921818915/job/140254070865) · [Windows](https://github.com/vixttha/LFVM/actions/runs/45921818915/job/140254071040) |

GitHub run/job API and decoded logs were read directly. Both runs completed successfully, all four jobs succeeded. Each job ran 101 tests in normal Python and 101 in optimized Python, each with OK and no reported skips: 808 test executions in total, not 808 unique tests. Ubuntu Python 3.14.4, Windows Python 3.12.10. The exact CI identity and both archive gates passed on every job. Prior failed Windows checkout evidence is retained in ORANGE-TEAM-DISPOSITION.md.

The additional repair rejects non-finite exponent values, malformed Unicode and excessive JSON nesting, fixes contract drift checks, bounds archive inventory enumeration, checks OOXML relationship identity and referenced target presence, requires every acceptance test on both public runner OSes, validates historical branch and initial version, bounds partition inventory and rejects scalar parser output, and strengthens public URL checks. Five shared files were read back with identical Git blob IDs across branches: foundation.py, qualification.py, test_foundation.py, test_qualification.py and foundation-contract.json.

## Complete disposition inventory

The verified foundation designation applies only to current prebuild controls, not production release security. The statuses below intentionally do not certify all 45 issues closed.

| Finding | Disposition | Evidence / remaining gate |
|---|---|---|
| LF-A01 | Verified foundation | Explicit failures survive optimized Python; both modes run. |
| LF-A02 | Verified foundation | Strict JSON, duplicate keys, exact schema types, overflow/surrogate and depth checks. |
| LF-A03 | Verified foundation | Current prebuild state allowlist and lock denial; future lifecycle transitions have synthetic coverage. |
| LF-A04 | Verified foundation | Exact initial active pointer and single checkpoint. |
| LF-A05 | Contained / pending production | Prebuild refuses approval/artifacts. Signed receipt primitives tested; external owner trust root and integration absent. |
| LF-A06 | Contained / pending production | No fake workbook counters accepted. Synthetic reports now require every test on both OSes; real qualification remains disabled. |
| LF-A07 | Contained / pending production | Original handoff anchored; accepted history inventory comparison tested synthetically, external accepted chain not configured. |
| LF-A08 | Contained / pending production | Initial predecessor fixed; numeric successor and trusted chain checks tested; release activation pending. |
| LF-A09 | Contained / pending production | Append-only supersession protocol documented; no accepted edition exists. |
| LF-A10 | Contained / pending production | Bounded package preflight; actual workbook structure and schema verification still required. |
| LF-A11 | Verified foundation | Archive path, symlink/reparse, normalized Unicode and collision checks; actual release package still requires independent inspection. |
| LF-A12 | Verified foundation | Exact prebuild archive and tracked spreadsheet denial; synthetic release inventory checks. |
| LF-A13 | Contained / pending production | 54 expected, zero imported enforced; source ID reconciliation tested on synthetic inputs, real snapshot not imported. |
| LF-A14 | Contained / pending production | Actual byte digest and mapping helper tested synthetically; no real snapshot authorized. |
| LF-A15 | Contained / pending production | Accounted/imported/excluded/duplicate/superseded and normalized offers separated by reconciliation helper; actual data edition pending. |
| LF-A16 | Contained / pending production | Dependency binding and signed template verification primitives tested; no accepted template or independent production adapter. |
| LF-A17 | Contained / pending production | Accepted schema digest parity primitive tested; actual workbook structural parity and migration pending. |
| LF-A18 | Verified foundation | Blocked states require null binding and zero import/approval. |
| LF-A19 | Verified foundation | Fixed exact contract v1 and explicit schema versions; future migration requires explicit version. |
| LF-A20 | Verified foundation | Separate template_schema/research_data namespaces; exact dependency protocol documented. |
| LF-A21 | Verified foundation | Five shared files match across branches, exact taxonomy/policy checked; future revisions require explicit protocol evolution. |
| LF-A22 | Verified foundation | 101 tests per mode on both operating systems and both branches. |
| LF-A23 | Verified foundation | Exact push run/job conclusions and logs independently retrieved for both code heads. |
| LF-A24 | Verified foundation | Manual dispatch reliance removed; exact push workflows confirmed. |
| LF-A25 | Configured / not live tested | PR workflow target and event validation implemented; no live PR run created under branch-only scope. |
| LF-A26 | Verified foundation | Pinned checkout and persist-credentials false in read-only workflow; actual jobs passed. |
| LF-A27 | Partially verified | Ubuntu Python 3.14.4 and Windows Python 3.12.10 ran successfully; explicit multi-version compatibility matrix not implemented. |
| LF-A28 | Partially verified | Bounded parsing, streaming artifact hashes, inventory and ZIP limits; real large workbook qualification still pending. |
| LF-A29 | Partially verified | Public text/URL scanner and synthetic credential checks; real publication review, complete secret coverage and trusted inputs not proven. |
| LF-A30 | Partially verified | CSV literal-escaping and package checks tested; actual workbook ingestion/formula policy pending schema. |
| LF-A31 | Contained / pending production | Separate owner/auditor signature primitives and exact scope/commit binding tested; production identities not provisioned. |
| LF-A32 | Partially verified | Non-force exact-head leases used and confirmed; recovery policy documented; actual migration failure injection pending. |
| LF-A33 | Deferred workbook/data dependency | Claim freshness and contradictory/billing policies need accepted schema and actual research. |
| LF-A34 | Partially verified | Synthetic partition counts/digests/global IDs at 100/1,000/10,000 rows; Excel parser and rollover protocol pending actual schema. |
| LF-A35 | Deferred owner policy | No license inferred or modified. |
| LF-A36 | Verified foundation | Push event/ref/SHA/ancestry validated on actual jobs; PR identity checked synthetically. |
| LF-A37 | Verified foundation | Nonempty required documents and manifest inventory checks; semantic instruction review remains manual. |
| LF-A38 | Verified foundation | Initial archive allowlist and canonical version grammar; later versions require new contract. |
| LF-A39 | Residual trust limitation | Candidate cannot self-approve under active gate; external verifier/trust roots required, branch is not protected. |
| LF-A40 | Verified foundation | Foundation metadata vs workbook qualification distinguished in receipt contract and tests. |
| LF-A41 | Deferred workbook/data dependency | No actual XLSX generation or rebuild/readback authorized. |
| LF-A42 | Verified foundation | Original 45-ID handoff and this exact-head retest record preserved in each branch; no independent runtime claimed. |
| LF-A43 | Separate workstream | Original 28 template design findings and seven filled readiness findings remain open; workbook creation not authorized. |
| LF-A44 | Partially verified | Bounded OOXML checks include internal relationship target existence, IDs, roots and active-part restrictions; complete schema/formula checks pending. |
| LF-A45 | Deferred workbook/data dependency | Actual staged migration/rollback tests need accepted template and actual import; no real workbook created. |

Counts: 19 Verified foundation; 12 Contained / pending production; 1 Configured / not live tested; 7 Partially verified; 3 Deferred workbook/data dependency; 1 Deferred owner policy; 1 Residual trust limitation; 1 Separate workstream. Total 45.

## Preserved constraints and next gate

Main still equals its initial commit de4503a783504dcdfc066482bfbf004e9b0287fe. Both v0.0.0.1 manifests remain unchanged: blank audit_pending with 28 open design findings, filled blocked_on_template with 54 expected and zero imported. Both workbook test counters remain zero. No XLSX, data import, paid infrastructure, self-approval or main merge. Real release requires an approved schema, exact external trust roots and independent evidence adapter, actual workbook and data verification, and prior acceptance gates. Keep fail-closed prebuild-only mode; do not fabricate approval or remove the block.

This report is a later documentation receipt for the tested code commits, not a self-referential attestation of its own commit. A subsequent documentation-only CI run must not be confused with workbook qualification.
