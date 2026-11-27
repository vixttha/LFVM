# Library of free virtual machines spreadsheet template version blanks

One folder per actual template checkpoint. This archive contains blank template versions only; the populated research library belongs elsewhere. Start at [AGENTS.md](AGENTS.md) (singular [agent.md](agent.md) is a navigation alias).

The machine-readable [versions.json](versions.json) is the archive index. The only current checkpoint is [v0.0.0.1](v0.0.0.1/README.md), still in planning/audit. Future version directories are created when work is authorized, not preallocated.

Each version directory holds README.md, PLAN.md, AUDIT.md, CHANGES.md, VALIDATION.md, manifest.json and, once built, the blank .xlsx artifact. CHANGES.md documents differences, improvements, regressions/degradations, tradeoffs and unmeasured effects. The first version has no predecessor. Locked versions are immutable; improvements go into successor folders.

Use exact artifact SHA-256 and commit-bound CI receipts before locking. Never put provider data in these blanks.
