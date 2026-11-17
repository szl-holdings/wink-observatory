# A10 diagnosis supersession (17 November 2026)

The append-only record `data/receipts/a10-diagnosis-supersession-20261117.json`
supersedes the causal interpretation in `data/receipts/a10-diagnosis.json`.
The original diagnosis, held-out receipt and all historical evidence remain unchanged.

The archived scorer uppercases output, extracts the first standalone A-D token,
and compares it with the answer key. Lowercase answers can score. A formatted
wrong option fails. Verbose answers can score. The metric conflates answer
correctness and format availability; it is not pure letter-format compliance.

The 0.05/0.05 summaries contain no per-item outputs. Format failures, truncation,
wrong answers and the effect of non-isolated arms cannot be separated. Below-chance
scores do not establish a scoring artifact, and a calculation assuming independent
arms cannot resolve a run whose archived base object already had its adapter
attached. The source-bound integrity amendment already states these limitations.

The preservation verdict remains **UNINTERPRETABLE** and the -0.05 acceptance
floor still cannot fail for any valid rate. No new model measurement or scientific
qualification is claimed. This correction concerns the legacy v1 receipt, not the
separate corrected-probe v2.1 runs.

The JSON binds the original diagnosis by SHA-256 and commit, and binds the archived
scorer by a full dataset revision and SHA-256. Its exact function excerpt is tested
with deterministic positive and negative examples:

```sh
python -B -m unittest discover -s tests -p 'test_a10_supersession.py' -v
python backend/validate.py
```

These checks establish source semantics and preservation of the old record, not
proof that the archived code executed. The source-only correction does not deploy
the Space, publish to the HF dataset, or notify any collaborator. Existing runtime
and data consumers still need explicit reconciliation before their diagnosis can
be called corrected.
