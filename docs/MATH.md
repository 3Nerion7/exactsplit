# Mathematical contract

Let `A` be the integer amount, `n` the number of active recipients, and `w[i]` their integer weights. The denominator is 10,000. Inputs satisfy `0 <= A <= 2^128−1`, `2 <= n <= 16`, `0 <= w[i] <= 10000` and `sum(w) = 10000`. Inactive slots have zero weight. The cursor is an index in `[0,n)`.

For each active recipient:

```text
product[i] = A * w[i]
floor[i]   = product[i] // 10000
residue[i] = product[i] % 10000
left       = A - sum(floor)
```

The sum of all residues is `left * 10000`. Each residue is below 10,000, so `0 <= left < n`. There are enough positive residues to assign the remaining units. Repeatedly select the largest unawarded residue and increase that recipient's floor by one.

Consequently:

* The payouts conserve exactly `A`; inactive payouts are zero.
* Every payout is either the floor or ceiling of its exact quota. Its absolute deviation from quota is below one integer unit.
* No recipient receives two residual units in one allocation.
* Zero weights receive zero units, including when `A < n`.

These statements describe the algorithm and the validated domain. The tests check examples and boundaries; they are not a machine-checked proof over every possible input.

## Bounds

Validated multiplication is below `2^128 * 10000 < 2^142`, safely inside `u256`. Weight summation is at most 160,000 even before checking its required total. After weight validation, partial floor sums cannot exceed `A`. The residual loop executes at most `n−1` times and scans at most 16 recipients per iteration.

The larger `u256` field types are deliberately not the accepted amount domain. Values above `2^128−1` are rejected before multiplication. `Units` and `BasisPoints` distinguish kinds; their public fields still require validation.

## Tie order and state

Fixed ranks index `i` by `i`. Rotating ranks it by `(i + n - cursor) % n`. Larger residues always win first; this order is used only for exact residue ties. The same initial cursor applies throughout one allocation.

In Rotating mode, the next cursor is the index immediately after the **last residual winner**. It remains unchanged if there are no residual units. Fixed preserves the cursor. `preview` returns this proposed value without an effect. `commit_split` requires mutable `RotationState` and writes only after receiving a successful preview.

For repeated identical rounds, this follows the boundary tie group instead of mechanically visiting recipients who cannot receive its residual unit. It is not a debt ledger across changing weights or amounts, a general fairness theorem, or an access-control mechanism. Applications own and persist their rotation state; they can also reset it.

## Known counterexample

Hamilton's method is not house-monotone. For weights `[5556,3333,1111]`:

| Total | Payouts |
|---:|---|
| 4 | `[2,1,1]` |
| 5 | `[3,2,0]` |

There is no tie to rotate away. A caller requiring that no recipient ever loses when the total increases needs a different allocation method. Changes to weights or recipient order can also change payouts. Recipient indices and cursor management must therefore be intentional application decisions.
