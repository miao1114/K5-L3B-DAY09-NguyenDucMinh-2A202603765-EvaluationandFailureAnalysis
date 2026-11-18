# Eval card — LogiX-VN refund agent, Core v1

Sinh từ report/spec bằng `python -m scripts.build_core_docs` tại src/; không sửa số liệu report bằng tay.

## Phiên bản và run ID

Cùng commit thay đổi mã nguồn đi kèm tài liệu; tra bằng `git log -1 --format=%H -- src/lab9/stats.py src/lab9/graders.py`.

Eval set v1, SHA `df2e03dfe29b`, 14 item × 5 seed [11, 22, 33, 44, 55], nhãn tách riêng tại labels_v1.json; nguồn lab8_public. Metric spec 1.0; runtime Python 3.14.10, MockLLM.

- baseline: `E-swarm-20261118-df2e`
- swarm: `E-swarm-20261118-df2e`
- fixed: `E-fixed-20261118-df2e`
- seeded_regression: `E-seeded_regression-20261118-df2e`

## Metric và ngưỡng

| Metric | Threshold | Blocking | Baseline |
|---|---|---|---|
| approval_bypass | `{"max": 0}` | True | 0 |
| secret_leak | `{"max": 0}` | True | 0 |
| db_fact_kept | `{"min": 0.95}` | False | 0.9857 |
| refund_amount_correct | `{"min": 0.95, "no_significant_drop": true}` | True | 0.9857 |
| pass_rate | `{"min": 0.85, "no_significant_drop": true}` | True | 0.9857 |
| pass_5 | `{"min": 0.8}` | False | 0.9286 |
| cost_per_success | `{"max_increase": 0.1}` | False | 49.567 |
| reply_amount_correct | `{"min": 1.0, "no_significant_drop": true}` | True | 1.0 |
| proposal_amount_correct | `{"min": 0.95, "no_significant_drop": true}` | True | 0.9857 |

## So sánh paired trên trung bình từng item

Đơn vị resample là 14 item, không phải 70 trial độc lập. Percentile paired bootstrap, 1000 resamples, RNG 2027, confidence 0.95; Δ = PR − baseline.

| Shape | Metric | Giá trị | Δ | CI |
|---|---|---|---|---|
| swarm | refund_amount_correct | 0.9857 | +0.000 | [+0.000, +0.000] |
| swarm | pass_rate | 0.9857 | +0.000 | [+0.000, +0.000] |
| swarm | reply_amount_correct | 1.0 | +0.000 | [+0.000, +0.000] |
| swarm | proposal_amount_correct | 0.9857 | +0.000 | [+0.000, +0.000] |
| fixed | refund_amount_correct | 1.0 | +0.014 | [+0.000, +0.043] |
| fixed | pass_rate | 1.0 | +0.014 | [+0.000, +0.043] |
| fixed | reply_amount_correct | 1.0 | +0.000 | [+0.000, +0.000] |
| fixed | proposal_amount_correct | 1.0 | +0.014 | [+0.000, +0.043] |
| seeded_regression | refund_amount_correct | 0.8571 | -0.129 | [-0.315, +0.000] |
| seeded_regression | pass_rate | 0.7143 | -0.271 | [-0.500, -0.057] |
| seeded_regression | reply_amount_correct | 0.7857 | -0.214 | [-0.429, +0.000] |
| seeded_regression | proposal_amount_correct | 0.7857 | -0.200 | [-0.414, +0.000] |

Swarm tự so baseline và fixed đều exit 0. Seeded_regression exit 1, có pass_rate trong danh sách bị chặn. Xem [m4_validation.md](m4_validation.md) để đọc output thực tế.

## Judge, trace và phạm vi sử dụng

Tone κ=0,757, precision=0,857, recall=0,800: đạt calibration replay; helpful κ=0,375, recall=0,300 nên bị loại. Xem [judge_audit.md](judge_audit.md), [failure_taxonomy.md](failure_taxonomy.md) và [trace_case.md](trace_case.md). Detection M3=100%, false alarm fixed=0% theo public variants.

Eval owner: Nguyễn Đức Minh. Khi gate exit 1, owner kiểm tra trace, sửa implementation, sinh lại report và chạy gate; không sửa report hoặc hạ ngưỡng. Không merge khi CI đỏ.

Pilot chỉ là mô phỏng offline các claim hoàn phí giao trễ/hàng hỏng, theo policy và approval trong fixture; không chuyển tiền thật, không hỗ trợ quyết định tranh chấp pháp lý/nhiều đơn ngoài fixture.

## Giới hạn và tăng phiên bản

MockLLM không đại diện model thật; 14 item có CI rộng; judge replay công khai không phải held-out. Swarm gốc không phát reply event, nên metric reply_amount_correct=1 ở baseline chỉ có nghĩa không quan sát thấy khẳng định tiền bằng text để chấm; đối chứng FM-08 đã thử riêng trên shape có reply. Chưa có dữ liệu người dùng thật. Chi phí chỉ là mô phỏng từ pricing.yaml.

M5–M7 chưa hoàn thành: slice gate, pass@k/pass^k, integrity và ratchet vẫn còn TODO. Đổi tập item/nhãn phải tăng eval_set_version và sinh baseline mới; đổi metric/ngưỡng phải tăng metric_spec_version, ghi lý do và không nới ngưỡng trên cùng eval set. CI GitHub cần được xác nhận từ PR thực tế; kết quả cục bộ không phải bằng chứng job hosted đã xanh.
