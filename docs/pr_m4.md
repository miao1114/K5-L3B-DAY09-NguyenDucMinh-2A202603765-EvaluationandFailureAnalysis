Swarm đã chạy được nhưng cần bộ đánh giá để chặn regression trước khi merge. PR hoàn thiện Core M1–M4: taxonomy/provenance, calibration và audit judge, trajectory graders (gồm so tiền reply với ledger), paired bootstrap và baseline v1.

Validation cục bộ: smoke PASS; evalset 0 problem(s); 46 test Core PASS; ci_check exit 0. Detection public variants 100%, false alarm fixed 0%. Swarm và fixed qua gate; seeded_regression bị chặn ở pass_rate với CI Δ khớp mốc bài lab. Mã nguồn Lab8 và src của dự án Day08 giữ nguyên. M5–M7 còn TODO.

Hosted job eval-gate cần được xác nhận trên PR này trước khi merge.

### swarm: exit 0

```text
gate: PR E-swarm-20261118-4d10 vs main E-swarm-20261118-4d10 · eval set 4d100783aa8e
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9857   {"min": 0.95}                                                         ok
  refund_amount_correct  0.9857   {"min": 0.95, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  pass_rate              0.9857   {"min": 0.85, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  pass_5                 0.9286   {"min": 0.8}                                                          ok
  cost_per_success       49.567   {"max_increase": 0.1}                                                 ok
  reply_amount_correct   1.0      {"min": 1.0, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  proposal_amount_correct 0.9857   {"min": 0.95, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
exit 0 — merge
```

### fixed: exit 0

```text
gate: PR E-fixed-20261118-4d10 vs main E-swarm-20261118-4d10 · eval set 4d100783aa8e
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           1.0      {"min": 0.95}                                                         ok
  refund_amount_correct  1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.014 CI [+0.000, +0.043] ok
  pass_rate              1.0      {"min": 0.85, "no_significant_drop": true} Δ +0.014 CI [+0.000, +0.043] ok
  pass_5                 1.0      {"min": 0.8}                                                          ok
  cost_per_success       48.7157  {"max_increase": 0.1}                                                 ok
  reply_amount_correct   1.0      {"min": 1.0, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
  proposal_amount_correct 1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.014 CI [+0.000, +0.043] ok
exit 0 — merge
```

### seeded_regression: exit 1

```text
gate: PR E-seeded_regression-20261118-4d10 vs main E-swarm-20261118-4d10 · eval set 4d100783aa8e
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9286   {"min": 0.95}                                                         warn
  refund_amount_correct  0.8571   {"min": 0.95, "no_significant_drop": true} Δ -0.129 CI [-0.315, +0.000] BLOCK
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
  pass_5                 0.7143   {"min": 0.8}                                                          warn
  cost_per_success       81.202   {"max_increase": 0.1}                                                 warn
  reply_amount_correct   0.7857   {"min": 1.0, "no_significant_drop": true} Δ -0.214 CI [-0.429, +0.000] BLOCK
  proposal_amount_correct 0.7857   {"min": 0.95, "no_significant_drop": true} Δ -0.200 CI [-0.414, +0.000] BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_correct, proposal_amount_correct
```
