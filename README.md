# ExactSplit

**Keep every integer unit. Make the tie policy explicit.**

ExactSplit is a small Fe library for dividing a bounded amount between 2–16 weighted recipients. It uses exact arithmetic and returns a plan whose payouts sum to the input amount. It can model cents, points or inventory units; it does not transfer funds.

Its Fe-specific distinction is the separation between a pure preview and an operation that requires an explicit mutable rotation-state effect. Amounts and weights also have different types. These types prevent accidental mixing; numerical bounds are validated at runtime.

## Try it

Requirements: Python 3.11+ and the pinned **Fe 26.5.0** executable on x86-64 Windows or Linux. Python uses only its standard library. The compiler is a free, portable download; no account, RPC, wallet or deployment is needed.

```sh
python scripts/verify.py --download-compiler
```

On Linux, use `python3` if that is your Python command. To use an already downloaded official executable:

```sh
python scripts/verify.py --fe /path/to/fe
```

The runner verifies the compiler's published SHA256 before executing it. It checks the library, runs **17 focused Fe tests and 494 independent-oracle vectors**, then checks three positive/negative compiler pairs. A successful run ends with:

```text
PASS all checks: 511 Fe runtime tests; 3 compiler pairs.
```

Generated tests and logs stay in `.artifacts/`; downloaded tools stay in `.tools/`. Neither directory belongs in a published source package. See [the verification method](docs/VERIFICATION.md).

## Two policies, one exact total

For each recipient, first calculate the floor of its exact quota. Award the remaining integer units to the largest fractional remainders. Each recipient receives at most one residual unit.

* **Fixed:** equal remainders prefer lower recipient indices.
* **Rotating:** equal remainders prefer cyclic order starting at a supplied cursor. The proposed next cursor follows the last recipient awarded a residual unit. No residual units means no cursor change.

Rotating changes only ties. It never gives a smaller remainder priority over a larger one.

With weights `[5000, 5000, 0]` and one unit per round:

| Round | Fixed payouts | Rotating payouts | Next rotating cursor |
|---|---|---|---:|
| 1 | `[1, 0, 0]` | `[1, 0, 0]` | 1 |
| 2 | `[1, 0, 0]` | `[0, 1, 0]` | 2 |
| 3 | `[1, 0, 0]` | `[1, 0, 0]` | 1 |
| 4 | `[1, 0, 0]` | `[0, 1, 0]` | 2 |

The third recipient's zero weight receives no allocation. Advancing a cursor by one position per round would instead give winners `0, 1, 0` over a three-round cycle. Following the last actual residual winner avoids that particular bias.

## API

[`src/lib.fe`](src/lib.fe) exports:

* `preview(amount, weights, len, mode, cursor) -> SplitResult`: pure computation; returns payouts and a proposed cursor.
* `commit_split(amount, weights, len, mode) -> SplitResult uses (state: mut RotationState)`: computes first and updates the application's cursor only on success.
* `Units`, `BasisPoints`, `TieBreak`, `Allocation`, `RotationState`, `SplitError` and `SplitResult`.

Inputs use a 16-slot array. `len` chooses 2–16 active slots; inactive weights must be zero. Active weights must individually be at most 10,000 and sum to 10,000. Amounts range from zero through `2^128−1`. The cursor must be below `len`, including in Fixed mode. Public wrapper fields are inputs to validation, not evidence that their contents are already valid.

[The walkthrough](docs/WALKTHROUGH.md) connects the API, state effect and observable examples. Errors leave rotation state unchanged.

## Limits worth understanding

The allocation rule is Hamilton's largest-remainder method; it is not a new algorithm. This project supplies a bounded Fe implementation, explicit state semantics and reproducible evidence.

Hamilton is **not monotone in the total**. With weights `[5556, 3333, 1111]`, total 4 gives `[2, 1, 1]`, while total 5 gives `[3, 2, 0]`. The last recipient loses a unit. Rotating ties cannot fix this example because its remainders are unequal. This library therefore makes no general fairness or long-term balance guarantee. Read [the mathematical contract](docs/MATH.md) before choosing the policy for an application.

Verification was executed on Windows with Fe's local EVM test backend. Host-native Windows execution is unsupported by this Fe release. The Linux download path is provided but has not yet been run for this project. No gas savings, production deployment or financial-service suitability is claimed.

## Provenance

Development began on November 3, 2026 for the [Fe Builders Challenge](https://fe-lang.org/contest/). The allocation implementation and project-specific test tooling were written for this project. Fe's compiler and standard library are external tooling. See [AI assistance and reused work](docs/PROVENANCE.md) and [third-party tooling](THIRD_PARTY.md).

License: [MIT](LICENSE).
