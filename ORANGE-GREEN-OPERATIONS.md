# Orange / Green Team operational hardening

Mission LFVM-FOUNDATION-AUDIT-001. This is a successor foundation repair, not a workbook acceptance. Preserve original handoff and retest records. The earlier report's 45 finding IDs remain canonical.

## Green controls

The standard GitHub-hosted runner matrix explicitly covers Ubuntu and Windows with Python 3.11 (declared minimum) and 3.14. Each job checks the exact revision and runs the suite under normal and optimized Python. Checkout and setup-python are pinned to immutable upstream commit IDs; credentials are not persisted. No paid runner, external account, or main write.

The shared read-only evidence checker scripts/operations.py validates the exact push commit, branch, workflow path, repository, run attempt, job matrix, runner labels, required successful steps, exact runtime identity and no-skip test counts. It hashes actual independently retrieved job logs and produces a foundation_metadata receipt only. A trusted external caller must retrieve the raw GitHub API run and attempt-scoped jobs and job logs, pin the expected commit and minimum test count, and use trusted verifier code. Do not trust a receipt supplied by the candidate. Metadata results cannot authorize workbook release, and this is not a production workbook evidence adapter.

## Recovery and publication

Use exact-head non-force leases, preserve original history, and read back both shared components and manifests after publication. If either branch moves before publication, stop and recompute the candidate from the new exact head. If one branch publishes and the other fails, keep the successful commit, block downstream release, record the split and reconcile the second branch from its actual head; never force-reset either. A corrective successor reverts faulty changes while preserving evidence. Compare both shared Git blobs before claiming compatibility. A future real data migration must stage output outside the accepted edition, reconcile every source ID, validate all partitions before atomic publication and test failure at each transition. No production migration currently exists.

## Boundaries

No real XLSX, provider records, production signing keys or actual release approval are created. Accepted workbook schema, externally trusted keys and independent workbook evidence retrieval, history authority, real source snapshot, actual workbook content qualification and license decisions remain separate gates. The earlier architecture/readiness findings must not be marked closed merely because foundation CI passes.
