# Blank template dependency contract

Authoritative blank agent branch: `library-of-free-virtual-machines-spreadsheet-template`. Its current v0.0.0.1 is audit_pending, with no workbook at setup. See [blank archive](https://github.com/vixttha/LFVM/tree/library-of-free-virtual-machines-spreadsheet-template/library%20of%20free%20virtual%20machines%20spreadsheet%20template%20version%20blanks). The current target is a dependency request, not acceptance.

Before filling any edition:
1. Read the blank version index and manifest at the exact commit. Require owner-locked status, implementation approval, a real .xlsx and artifact SHA-256 plus qualification evidence and owner acceptance.
2. Fetch the workbook by immutable commit/path; verify bytes against digest. Record template version, commit, path, digest, schema and acceptance evidence in data manifest. Do not bind only to the moving branch head.
3. Copy the blank artifact into a working area, populate only authorized data tables using its dictionary, taxonomy and partition protocol; validate no structural drift. Never overwrite the original blank.
4. If a data need cannot be represented, report it to the template agent. Use no ad hoc columns or silent coercion. An accepted successor template and migration plan must be approved; preserve IDs, history and source-to-target reconciliation.
5. Data edition and template version are independent. A new provider does not require a new template release; an accepted template upgrade does not silently rewrite earlier data releases.

No import until dependency is satisfied and owner authorizes the import. This contract is a policy; the metadata validator checks completeness of bindings, not external owner approval or workbook contents. Candidate qualification must verify those separately.
