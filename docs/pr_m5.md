Complete Advanced M5–M7 so the gate catches localized regressions, intermittent failures, and corrupted evaluation evidence. Keep the 14-item v1 dataset and Core reports unchanged; v2 adds the supplied adversarial pack and frozen slice thresholds.

Implement pass@k/pass^k with invalid-input checks and choose blocking pass_hat_5>=0.85 after A/A delta=0 (baseline 0.8929, flaky 0.5714). Metric spec 2.1 adds this reliability guard without loosening M5 thresholds.

Integrity rejects duplicate/missing rows, changed seeds/slices, None/NaN/inf, evaluator failures, and aggregate values inconsistent with rows. Ratchet protects metric/slice thresholds, blocking, and no_significant_drop. CI checks the trusted base spec once the first v2 baseline is published. Supplied variants, traps, tests, Lab8 and the separate Day08 source remain unchanged.

Validation: 90 M1–M7 student tests pass locally. Mutation 3/3 regressions blocked, 0/2 false alarms; all 4 public traps plus 2 additional evidence checks rejected. Quiet fact corruption with no override event is blocked using outcomes. Reports/documents are script-generated. Hidden grading is not available.

| Shape | Expected | Blocked metrics |
|---|---|---|
| fixed | merge | none |
| honest_refactor | merge | none |
| seeded_regression | block | refund_amount_correct, pass_rate, pass_hat_5, reply_amount_correct, proposal_amount_correct, slice:money_movement/pass_rate, slice:adversarial/pass_rate, slice:denial/pass_rate |
| slice_regression | block | slice:money_movement/pass_rate |
| flaky_regression | block | pass_rate, pass_hat_5, proposal_amount_correct, slice:money_movement/pass_rate |

```text
pass_hat_5 baseline=0.8929 flaky=0.5714 floor=0.85
A/A: all metric deltas=0 for 11,22,33,44,55 vs 66,77,88,99,110
evaluator_errors_as_nan: exit 1 — INTEGRITY
dropped_failing_rows: exit 1 — INTEGRITY
cherry_picked_seeds: exit 1 — INTEGRITY
loosened_spec: exit 1 — INTEGRITY
```

See docs/m67_cli.txt for official mutation/A/A/trap CLI output and docs/m67_validation.md for detailed rejection reasons. Wait for all hosted CI jobs to pass before merging.
