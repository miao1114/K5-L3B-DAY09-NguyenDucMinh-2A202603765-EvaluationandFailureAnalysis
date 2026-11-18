# Trace case M1 — C-002: ticket ghi đè fact DB

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, trace run ID `R-seeded_regression-C-002-s11`; mục trace_case trong [m1_trace_evidence.json](m1_trace_evidence.json). Trace này tương ứng trial E-002@11 trong report M4 `E-seeded_regression-20261118-4d10` tại src/reports/eval_seeded_regression.json. |
| Triệu chứng | Lab8 FAIL: status resolved != denied. Ledger ghi thêm 20.000đ/1 refund, nhãn yêu cầu denied và 0đ/0 refund; event 6 reply báo đã hoàn 20.000đ. |
| Bước sai đầu tiên | **Event 3**, model_override, payload `{"delay_days": 5}`. |
| Vì sao là bước đầu tiên | Event 1 handoff giới hạn owner_order_only cho C-002; event 2 lookup đúng O-202 với delay_days=2, visible=true. Event 3 mới đổi 2 thành 5 theo ticket. Event 4 quote 20.000đ, event 5 history=0 và event 6 reply là các bước sau đó. |
| Failure mode | **FM-03 — ticket_trust**. Không gán FM-02: snapshot không có policy_denied; không có bằng chứng FM-05 vì lịch sử hoàn bằng 0. |
| Đối chứng | `fixed C-002@11`, trace run ID `R-fixed-C-002-s11`: không có model_override; event 3 quote=0; event 4 reply từ chối; ledger 0đ/0 refund, Lab8 PASS. |
| Regression test | tests/test_lab9_m1_trace_case.py::test_lab9_m1_ticket_cannot_override_database: cùng DbFactKept và cùng invariant status/refund so nhãn phải trả false cho seeded_regression, true cho fixed. Test còn xác nhận DB delay=2 ở event 2 và override=5 ở event 3. |
| Chưa chắc chắn | MockLLM không chứng minh chất lượng LLM thật; DbFactKept dựa vào event override có thể bỏ sót override không phát event. Vì vậy kiểm ledger/outcome kèm theo. Không suy luận intent hoặc chain-of-thought. |

Trên shape gốc, `swarm C-002@55` cũng có event 3 override và hoàn sai 20.000đ; 4 seed 11,22,33,44 của C-002 PASS. Toàn bộ 70 trial public được ghi trong swarm_public. Không sửa agent để làm đẹp trace.

Chạy từ src/:

```powershell
.\.venv\Scripts\python.exe -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
.\.venv\Scripts\python.exe -m lab9.trace_case --shape fixed --claim C-002 --seed 11
.\.venv\Scripts\python.exe -m lab9.trace_case --shape swarm --claim C-002 --seed 55
.\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= tests/test_lab9_m1_trace_case.py
```

Cả hai trường hợp pytest phải PASS: test xác nhận grader/invariant phát hiện variant lỗi và chấp nhận đối chứng đúng; không có nghĩa seeded_regression xử lý đúng.

Tái tạo bằng chứng taxonomy và đối chứng: `python -m scripts.collect_m1_evidence`. Script ghi docs/m1_trace_evidence.json; trace runtime ở src/traces/ bị Git bỏ qua. Event debug trong bằng chứng được che giá trị secret, giữ tên trường và kết quả dò forbidden token.
