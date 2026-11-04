# Reproducing the evidence

Run `python scripts/verify.py --download-compiler`, or provide an existing official executable with `--fe PATH`. Python 3.11+ uses no third-party packages. The runner pins Fe 26.5.0 and checks its size and SHA256. It supports x86-64 Windows and Linux; this project's recorded execution is Windows with the local EVM backend.

## Runtime checks

The 17 handwritten Fe tests cover input errors, the amount boundary, inactive recipients, conservation, rotation, capability-backed state changes, failure without state mutation and Hamilton's non-monotonic example.

[`scripts/oracle.py`](../scripts/oracle.py) generates 494 deterministic vectors. It does not reproduce the Fe implementation's repeated winner selection. Instead it enumerates quota-feasible floor/ceiling allocations, retains those conserving the total and minimizes their exact squared error. A lexicographic key resolves equal-cost candidates under the required fixed or cyclic priority. Exact rational quotas and integer-scaled error avoid floating point.

The test-only enumeration is exponential in recipient count. It is intentionally a bounded reference, not a replacement production algorithm. Vectors cover every supported active length, both policies, sparse weights, small amounts, ties and large amounts. Randomized-looking examples use a fixed integer generator so regeneration is reproducible.

The runner refuses modified or stale [`fixtures/vectors.json`](../fixtures/vectors.json) unless it matches independent regeneration. [`scripts/generate_tests.py`](../scripts/generate_tests.py) then creates a disposable Fe ingot whose assertions compare actual Fe outputs and next cursors with those vectors. It also checks inactive slots and the total. All 494 cases execute in Fe; producing expected JSON alone is not a passing run.

## Compiler checks

Three paired examples check distinct amount/weight types, the required rotation effect and its mutability. Each positive control must compile. Its negative counterpart must exit with code 1 and the precise expected diagnostic; an unrelated parse, dependency or manifest failure does not pass. Sources are stored as `.fe.txt` and materialized into separate disposable ingots.

## Reading the result

The expected successful summary is **511 Fe runtime tests and three compiler pairs**. Logs and `.artifacts/verification.json` include the compiler hash, exit codes, runtime counts and source hashes. A failed run writes `passed: false`; inspect its error and logs. A previous successful log is not evidence for changed source files.

Review fixture changes before explicitly regenerating them with `python scripts/oracle.py --write-vectors`. Keep generated artifacts, local tool binaries and private machine paths out of a published package. Successful tests support the stated contract; they do not establish production financial correctness, a formal proof or contest selection.
