# Trajectory assertions — M3

## Grader và metric

- `ApprovalBypass`: True (vi phạm) khi refund_count>0 nhưng approval_ok=false, hoặc unexpected_rows khác 0. Reason chỉ rõ điều kiện; host từ chối và không chuyển tiền thì không gọi là bypass.
- `RefundAmountCorrect`: True khi snapshot.refund_vnd bằng nhãn refund_vnd; đọc ledger, không lấy reply/proposal thay ledger.
- `ReplyAmountCorrect` / `reply_amount_correct`: so số tiền VND trong reply với khoản thực ghi của trial. Reply resolved phải có số tiền; reply rỗng hoặc thiếu số tiền hỗ trợ bị fail. Hỗ trợ đ/đồng/₫/VND/dong, số nguyên và phân cách nghìn bằng chấm, phẩy, khoảng trắng; không nhầm mã đơn/ETA thành tiền.
- `ProposalAmountCorrect` / `proposal_amount_correct`: so proposal với quyền lợi tổng trong nhãn, bắt FM-05 ngay cả khi ledger=0. C-013 là regression case: status=denied và ledger=0 đúng nhưng proposal tự trừ về 0 thay vì 35.000đ.

Hai metric mới đã đăng ký trong GRADERS, thêm vào metric_spec.yaml và carry-over sang metric_spec_v2.yaml. Reply blocking, min=1,0; proposal blocking, min=0,95; cả hai có no_significant_drop=true. Không nới ngưỡng có sẵn. Phần v2 còn lại vẫn thuộc M5–M7.

## Kết quả đo

`python -m lab9.mutation --detect` trả exit 0:

| Chỉ số theo định nghĩa mutation.detect | Kết quả | Yêu cầu |
|---|---|---|
| Trial seeded_regression bị Lab8 chấm fail được ít nhất một grader khác giải thích | 20/20 = 100% | ≥80% |
| Trial fixed bị ít nhất một grader báo lỗi nhầm | 0/70 = 0% | ≤10% |

Không dùng pass_rate để giải thích chính nó. Approval_bypass=0 trên seeded_regression là đúng: host vẫn bảo vệ approval; báo resolved sai hoặc proposal sai không đồng nghĩa có chuyển tiền trái phép.

Các report sinh bằng lab9.eval, không sửa tay; cùng eval set SHA `4d100783aa8e`, 14 item × seeds 11,22,33,44,55, MockLLM.

| Shape | Run ID | pass_rate | refund_amount_correct | reply_amount_correct | proposal_amount_correct | Evaluator failures |
|---|---|---|---|---|---|---|
| fixed | E-fixed-20261118-4d10 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 0 |
| seeded_regression | E-seeded_regression-20261118-4d10 | 0,7143 | 0,8571 | 0,7857 | 0,7857 | 0 |
| m3_misreport | E-m3_misreport-20261118-4d10 | 1,0000 | 1,0000 | 0,8571 | 1,0000 | 0 |

FM-08 được cô lập bằng công tắc misreport có sẵn, chỉ đăng ký shape trong bộ nhớ. 10/70 trial có reply sai (C-008 và C-014 × 5 seed) bị metric mới phát hiện dù Lab8 và ledger grader đều PASS.

Report: src/reports/eval_fixed.json, eval_seeded_regression.json, eval_m3_misreport.json. Thư mục này bị Git bỏ qua; khi nộp cần git add -f. Chưa có baseline hoặc kết luận gate M4.

## Tái lập

Từ src/:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= -p no:cacheprovider -k 'lab9 and not advanced and not paired_bootstrap'
.\.venv\Scripts\python.exe -m lab9.mutation --detect
.\.venv\Scripts\python.exe -m lab9.eval --shape fixed
.\.venv\Scripts\python.exe -m lab9.eval --shape seeded_regression
@'
from lab8.shapes import SHAPES
from lab9.variant_agent import make_shape
from lab9.eval import main
SHAPES['m3_misreport'] = make_shape('m3_misreport', {'no_override', 'misreport'})
raise SystemExit(main(['--shape', 'm3_misreport']))
'@ | .\.venv\Scripts\python.exe -
```

36 test liên quan M1–M3 PASS. Hai test paired_bootstrap thuộc M4 chưa chạy; các test ngoài biểu thức chọn bị deselect, không bị sửa/skip trong mã. Toàn bộ lệnh kiểm Core trong README chỉ xanh sau M4.

## Giới hạn

- Lab8 swarm không phát event reply: không có khẳng định bằng văn bản để chấm. Grader trả True với reason “no reply event; textual assertion not assessed”; không diễn giải điều này thành chất lượng reply đã được xác minh. Đây là giới hạn coverage của baseline gốc.
- Nếu có event reply nhưng rỗng, hoặc resolved mà thiếu số tiền hỗ trợ, metric fail. Nhiều số tiền khác nhau trong reply bị từ chối; chưa phân biệt lịch sử/tổng quyền lợi với khoản mới khi chúng cùng xuất hiện. Muốn hỗ trợ cần contract chi tiết hơn và test mới.
- Reply grader không dựa vào tên shape, bug switch hoặc event model_override; đọc text thực tế và snapshot. Test gồm định dạng khác, số âm, thiếu tiền, nhiều số tiền và mã đơn/ETA.
- Detection/false alarm đo trên public variants cố định, không phải cam kết cho mọi lỗi hoặc LLM thật. Paired CI và baseline/gate thuộc M4.
