# Reproducing the evidence

Run `python scripts/verify.py --download-compiler`, or provide an existing official executable with `--fe PATH`. Python 3.11+ uses no third-party packages. The runner pins Fe 26.5.0 and checks its size and SHA256. Recorded executions cover x86-64 Windows and Ubuntu 24.04 under WSL2, using Fe's local EVM backend.

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

## Recorded Linux execution

On November 16, 2026, the unmodified project at `a310f86eb83b71f70cdbe4ec8ea377352a9c5f44` was verified on Ubuntu 24.04 x86-64 under WSL2 with Python 3.12.3. The official Fe 26.5.0 Linux executable matched the pinned SHA256 and size. `python3 scripts/verify.py --download-compiler` returned status 0: 17 focused tests, 494 independent-oracle vectors, and all three positive/negative compiler pairs passed.

[The compact record](evidence/linux-26.5.0.json) contains the observed counts, expected and actual exit codes, compiler identity and hashes of the tested code and fixtures. It was produced by the development tools, without a CI run or a new Windows execution. The earlier Windows passing report has matching code hashes. This documentation-only follow-up preserves the tested implementation, runner and fixtures.

The Linux execution used WSL2 and the EVM backend. It does not establish bare-metal or native-Fe application execution, deployment, performance or gas savings, production suitability, formal correctness, or contest eligibility.
