# LFVM Test Vault

This dedicated LFVM branch contains the pinned Lydite starter and LFVM's planned verification catalog. Start at [Test Vault](test-vault/README.md), [LFVM cases](test-vault/cases.md) and [context](LFVM-CONTEXT.md).

The [permanent workflow](.github/workflows/test-vault.yml) runs on changes to this branch and pull requests targeting it, using standard public GitHub runners. It checks the real catalog, rejects malformed and duplicate rows, and exercises shared evidence in a disposable synthetic Git checkout. Those examples are not workbook execution receipts or proof of any provider offer. The original installation receipt remains historical; the new validation runs identify the exact checkout.

No workbook build, release or cross-branch modification is authorized by this workflow.
