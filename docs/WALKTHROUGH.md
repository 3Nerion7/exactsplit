# Follow one allocation

The inputs are an amount, a fixed-size weight array, an active length, a tie policy and a cursor. [`src/tests.fe`](../src/tests.fe) contains executable examples using the actual API.

## An exact budget

Ten units and four equal weights give quotas `2.5,2.5,2.5,2.5`. The floors consume eight units, leaving two. Fixed awards the two remaining units to indices 0 and 1: `[3,3,2,2]`. A Rotating cursor of 2 instead yields `[2,2,3,3]`; both conserve ten.

Run the relevant tests with the Fe executable selected for the verifier:

```sh
fe test --filter fixed_equal_weights_preserve_total_and_inactive_zero .
fe test --filter rotating_multiple_residuals_advance_after_last_winner .
```

Replace `fe` with its full executable path if it is not on PATH. These examples run in Fe's local EVM harness, not on an external chain.

## Pure planning versus advancing a round

`preview` has no rotation-state effect. It reports a proposed next cursor and leaves the application free to inspect or reject the plan. Calling it twice with identical inputs returns the same result.

`commit_split` declares `uses (state: mut RotationState)`. A caller must supply that capability. It first performs the same validation and calculation as preview. On success it stores the proposed cursor; on error it returns the error without changing the stored cursor. This is the reason for the effect: previewing an allocation and advancing the next round are different application operations.

The `preview_is_pure_and_commit_alternates_partial_ties` test gives weights `[5000,5000,0]` and commits four one-unit rounds. The first two recipients alternate; the third remains at zero. `errors_do_not_mutate_cursor` verifies the failure path.

The paired compiler fixtures provide a second kind of evidence: a caller without the required effect, or with a read-only effect, is rejected before execution. This restriction governs the call to `commit_split`; it does not prevent an application from editing its own public state elsewhere.

## Choosing a policy

Use Fixed for a stable index priority. Use Rotating when carrying the cursor between rounds is part of the application's intended tie policy. Neither policy promises that raising a future total can never reduce an individual payout. The executable `hamilton_is_not_house_monotone` example makes that limitation visible.
