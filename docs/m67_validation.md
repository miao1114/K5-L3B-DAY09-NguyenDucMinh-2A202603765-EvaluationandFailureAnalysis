# M6/M7 — Reliability và integrity

Sinh bằng `python -m scripts.verify_m67` từ src/.

Baseline `E-swarm-20261118-b6e7`, eval set SHA `b6e7b6bb68b6`, spec 2.2.

## M6

pass@k = 1 − C(n−c,k)/C(n,k); pass^k = C(c,k)/C(n,k). Từ chối n≤0, c ngoài [0,n], k ngoài [1,n], số không nguyên và boolean. Test đối chiếu phép liệt kê mọi mẫu nhỏ.

A/A: seeds [11, 22, 33, 44, 55] và [66, 77, 88, 99, 110]; mọi Δ = 0 trên MockLLM. Baseline pass^5=0.8929; sàn blocking=0,85, cách baseline 0,0429, nằm ngoài nhiễu quan sát bằng 0. Flaky pass^5=0.5714 bị chặn.

Với LLM thật, decoding, hạ tầng và judge có thể gây dải nhiễu >0; cần A/A độc lập và ngưỡng ngoài dải đó. Năm seed không bảo đảm bắt ổn định lỗi hiếm khoảng 1/3 seed hoặc hiếm hơn; không hạ ngưỡng theo từng variant để làm đẹp scorecard.

## Mutation scorecard

| Shape | Kỳ vọng | Metric chặn |
|---|---|---|
| fixed | merge | none |
| honest_refactor | merge | none |
| seeded_regression | block | refund_amount_correct, pass_rate, pass_hat_5, reply_amount_correct, proposal_amount_correct, slice:money_movement/pass_rate, slice:adversarial/pass_rate, slice:denial/pass_rate |
| slice_regression | block | proposal_amount_correct, slice:money_movement/pass_rate |
| flaky_regression | block | pass_rate, pass_hat_5, proposal_amount_correct, slice:money_movement/pass_rate |

Mutation score 3/3; false alarm 0/2. Baseline tự so chính nó qua gate. Quiet fact probe không phát override (db_fact_kept=1) vẫn bị chặn qua outcome/proposal; không sửa các variant được cung cấp.

## M7

Kiểm tra cả PR và baseline: đủ tích item×seed, không trùng, không thiếu/đổi seed, slice đúng dataset và nhất quán giữa seed; không NaN/inf hoặc score thiếu; evaluator_failures phải rỗng; recompute aggregate từ rows để bắt số tổng bị làm đẹp. Ratchet giữ min/max/max_increase, blocking, metric, slice và no_significant_drop khi dùng --base-spec trên cùng eval_set_version.

### evaluator_errors_as_nan: exit 1 — INTEGRITY

```text
  INTEGRITY PR: missing/nonfinite/invalid row metric refund_amount_correct
  INTEGRITY PR: missing/nonfinite/invalid row metric pass_rate
  INTEGRITY PR: missing/nonfinite/invalid row metric proposal_amount_correct
```

### dropped_failing_rows: exit 1 — INTEGRITY

```text
  INTEGRITY PR: row count differs from items x seeds
  INTEGRITY PR: incomplete item x seed coverage
  INTEGRITY PR: nonfinite/missing aggregate metric pass_hat_5
  INTEGRITY PR/baseline (item, seed) sets differ
```

### cherry_picked_seeds: exit 1 — INTEGRITY

```text
  INTEGRITY PR: manifest seeds differ from spec
  INTEGRITY PR: nonfinite/missing aggregate metric pass_hat_5
  INTEGRITY PR/baseline (item, seed) sets differ
```

### loosened_spec: exit 1 — INTEGRITY

```text
  INTEGRITY ratchet: db_fact_kept loosened min
  INTEGRITY ratchet: refund_amount_correct loosened min
  INTEGRITY ratchet: refund_amount_correct removed no_significant_drop
  INTEGRITY ratchet: pass_rate loosened min
  INTEGRITY ratchet: pass_rate removed no_significant_drop
  INTEGRITY ratchet: pass_hat_5 loosened min
  INTEGRITY ratchet: reply_amount_correct loosened min
  INTEGRITY ratchet: reply_amount_correct removed no_significant_drop
  INTEGRITY ratchet: proposal_amount_correct loosened min
  INTEGRITY ratchet: proposal_amount_correct removed no_significant_drop
  INTEGRITY ratchet: removed slices money_movement
  INTEGRITY ratchet: removed slices adversarial
  INTEGRITY ratchet: removed slices denial
```

### duplicate_green_row: exit 1 — INTEGRITY

```text
  INTEGRITY PR: duplicate (item, seed) rows
  INTEGRITY PR: incomplete item x seed coverage
  INTEGRITY PR: aggregate pass_at_5 disagrees with rows
  INTEGRITY PR: aggregate pass_hat_5 disagrees with rows
  INTEGRITY PR: aggregate cost_per_success disagrees with rows
  INTEGRITY PR/baseline (item, seed) sets differ
```

### green_evaluator_failure: exit 1 — INTEGRITY

```text
  INTEGRITY PR: evaluator_failures must be an empty list
```

### deleted_pass_k_forged_reliability: exit 1 — INTEGRITY

```text
  INTEGRITY ratchet: removed pass_k estimates
  INTEGRITY PR: aggregate pass_hat_5 disagrees with rows
```

## Tái lập

```powershell
python -m pytest -q -m student -o addopts= -k lab9
python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110
python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json
python -m lab9.traps --pr reports/eval_v2_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
python -m scripts.verify_m67
```

Giới hạn: đây là vector public và các kiểm tra bổ sung tự xây, không phải bộ chấm ẩn. Gate không xác thực chữ ký/nguồn gốc trace; cần baseline và code grader do CI/reviewer tin cậy. --base-spec phải lấy từ nhánh gốc được bảo vệ, không tin một file tùy ý do PR đưa vào. Không khẳng định điểm rubric trước khi giảng viên chạy bộ ẩn.
