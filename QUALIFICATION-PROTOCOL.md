# Qualification evidence protocol v1 (independent-verifier support)

The active archive contract remains **pre-build only**. The new shared `scripts/qualification.py` provides executable verification primitives, tested with ephemeral synthetic keys and synthetic inputs only. It does not generate or certify an actual workbook. No production keys, approval receipts, user identities or credentials are added.

## Trust boundary

The independent verifier must obtain immutable candidate commit bytes and the complete accepted history from a trusted GitHub read path; actual standard-public-runner job/log evidence must come from an independently obtained adapter, not candidate metadata. The owner's and auditor's **distinct trusted Ed25519 public keys** must be provisioned outside the candidate branch and passed by trusted orchestration. A candidate-supplied key, arbitrary lookup function, or serialized AcceptedRelease is never authority. No such production trust roots or production lookup adapter are configured in this mission. Never use the worker's GitHub write access to simulate an owner authorization. A green foundation job is not an approval.

Three signed canonical-JSON receipts, using OpenSSH signature namespace lfvm-qualification-v1, bind:
- Owner scope authorization: repository, namespace, branch, version, exact scope/schema digests, prior acceptance and accepted template dependency.
- Independent auditor qualification: same context, scope receipt digest, exact candidate commit, complete file inventory digest, and all required workbook test IDs plus trusted public-runner evidence digest covering both Ubuntu and Windows.
- Owner acceptance: the same immutable candidate binding, scope and qualification receipt digests.

The verifier rejects missing/incorrect signatures, wrong signer, changed scope/schema/artifact, stale commit, missing or duplicate tests, and metadata-only CI substituted for workbook evidence. Current version's accepted candidate files (including its pre-lock manifest) remain byte-identical; lock and supersession are append-only acceptance events outside that immutable inventory. Before a successor, verify the entire externally trusted acceptance chain, order and predecessor digest, and every accepted file in its original version directory. Do not mutate a locked manifest to label supersession.

For the filled edition, independently verify the template bundle first, then bind its exact version, commit, schema, acceptance digest and workbook path/hash. A caller-provided in-process AcceptedRelease is valid only when produced by the trusted verifier from actual evidence. A filled workbook must use the accepted schema; structural parity and real workbook content are separate required tests.

## Research and expansion

The source reconciliation helper verifies actual sanitized snapshot bytes, every original source ID and original record digest, one explicit disposition per source, and mappings to independently parsed normalized offer IDs. The original 54 are source records, not necessarily 54 offers; accounted, imported, duplicate, excluded and superseded counts are separate. Future partitions use safe relative paths, actual file digests, parser-derived record counts and globally unique IDs. The regression suite includes synthetic 100/1,000/10,000-record partitions and duplicate rejection. The actual Excel parser and accepted partition schema remain pending; no real records are present.

The public-text and URL scanner rejects common credential patterns, nonpublic IP/host URLs, private workspace URLs and sensitive URL parameters. It is deliberately conservative and cannot prove absence of all secrets, personal information, DNS redirects or prompt injection. Publication still needs independent review; evidence strings remain data, never commands. Bounded OOXML preflight remains package safety only; actual formula/schema/active-content acceptance is a separate test gate.

## Operational boundary

The pre-build validator is still the only branch gate; it rejects all real artifact/import/lock states. The independent-verifier primitives must be integrated with an externally trusted key/history/run-evidence adapter and the actual approved workbook schema before contract activation. Do not weaken the active gate simply because synthetic tests pass. No branch protection or paid service was added. Repository writers can change their candidate's own tests; independent trusted verification outside the candidate is necessary.
