# Judge audit — M2

## Kết quả calibration trên dữ liệu replay gốc

FAIL là lớp dương: TP = judge bắt đúng lỗi; FP = báo lỗi nhầm; FN = bỏ sót lỗi; TN = cho qua đúng. Ngưỡng giữ nguyên: κ≥0,6; precision≥0,8; recall≥0,7. Quyết định dùng số chưa làm tròn; bảng chỉ hiển thị 3 chữ số.

| Tiêu chí | n | TP | FP | FN | TN | κ | Precision | Recall | Đạt floors? | Quyết định |
|---|---|---|---|---|---|---|---|---|---|---|
| tone_ok | 100 | 24 | 4 | 6 | 66 | 0,757 | 0,857 | 0,800 | Có | Dùng để đánh giá tone trong phạm vi calibration replay này. |
| helpful | 100 | 9 | 0 | 21 | 70 | 0,375 | 1,000 | 0,300 | Không | Loại khỏi quyết định chất lượng tổng thể/gate hiện tại. |

Tone có precision cao nhưng còn bỏ sót 6/30 lỗi (20%); không thể thay kiểm tra tiền, approval hoặc ranh giới dữ liệu bằng tone. Helpful có precision=1 vì 9 lần báo lỗi đều đúng, nhưng bỏ sót 21/30 lỗi (70%) và κ dưới 0,6; không đủ tin cậy để chặn regression.

## Hiệu chỉnh Rogan–Gladen

Dùng sensitivity = recall = TP/(TP+FN), specificity = TN/(TN+FP), p_obs = (TP+FP)/n và p_corr = (p_obs + specificity − 1)/(sensitivity + specificity − 1), cắt về [0,1].

| Judge | p_obs | Sensitivity | Specificity | p_corr | Tỷ lệ FAIL theo nhãn người |
|---|---|---|---|---|---|
| tone_ok | 0,280 | 0,800 | 66/70 ≈ 0,943 | 0,300 | 0,300 |
| helpful | 0,090 | 0,300 | 1,000 | 0,300 | 0,300 |

Hiệu chỉnh tỷ lệ tổng không sửa quyết định từng item và không làm helpful đạt floors. Vì các tham số được ước lượng trên chính tập replay này, p_corr khớp tỷ lệ nhãn người không phải bằng chứng tổng quát hóa sang tập mới. Hàm từ chối rate không hữu hạn/ngoài [0,1] hoặc sensitivity+specificity≤1; calibration biểu diễn correction không xác định bằng NaN. κ không xác định cũng phải FAIL calibration.

## Audit bất đồng và hành động sửa rubric

Đây là phân tích các dòng CSV và ghi chú được cung cấp, không phải một đợt gán nhãn người độc lập. H-* thuộc judge_tone_public.csv; HL-* thuộc judge_helpful_public.csv. Nhãn trong fixture gốc được giữ nguyên để tái lập số liệu.

| Case | Judge nói | Người nói | Ai đúng theo bằng chứng hiện có? | Phân tích và hành động sửa rubric |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Người | “Em… rồi nha… check giúp em” quá suồng sã theo quy chuẩn LogiX. Bổ sung ví dụ FAIL cho xưng hô thiếu chuẩn; mặc định LogiX/anh-chị, không coi thân thiện đồng nghĩa phù hợp. |
| H-017 | PASS | FAIL | Người theo note về khách lớn tuổi | “Bạn ơi… rồi nha” không hợp ngữ cảnh fixture. Rubric xét xưng hô và bối cảnh; không tự suy tuổi khách nếu đầu vào không có thông tin. |
| H-029 | PASS | FAIL | Người | “Không cần nhắn thêm” mang tính đóng hội thoại/ra lệnh dù mở đầu bằng “Dạ”. Chấm cả nội dung, thêm ví dụ phản chứng để tránh chỉ dò từ lịch sự. |
| H-042 | FAIL | PASS | Người | Câu ngắn vẫn lịch sự và có thông tin. Bỏ yêu cầu xin lỗi bắt buộc cho mọi reply; không phạt độ ngắn khi đủ ý. |
| H-051 | FAIL | PASS | Người | Từ “refund” được CS LogiX cho phép theo note. Thêm từ vựng nghiệp vụ cho phép; không đánh FAIL chỉ vì một từ tiếng Anh. |
| H-063 | PASS | FAIL | Người theo note | Hứa “sẽ hoàn thêm” ngoài kết quả hệ thống. Tách tiêu chí cam kết không có căn cứ; đối chiếu kết quả host bằng code cho quyết định tiền, không suy đúng tiền từ văn phong. |
| H-070 | PASS | FAIL | Người | Emoji cười không phù hợp khiếu nại. Bổ sung ví dụ FAIL về emoji/giọng đùa trong ngữ cảnh nhạy cảm. |
| H-081 | FAIL | PASS | Judge theo note của fixture; cần tái thẩm định nhãn | Note ghi người đọc nhầm ticket. Ghi đề xuất sửa human thành FAIL trong bản nhãn mới sau kiểm ticket/ledger; không sửa CSV gốc và không khẳng định tự xác minh ticket từ reply đơn lẻ. |
| H-088 | FAIL | PASS | Người | Lặp “Dạ” do lỗi gõ nhỏ, vẫn lịch sự. Cho phép lỗi gõ không đổi nghĩa; không quy mọi lỗi hình thức thành lỗi tone. |
| H-094 | PASS | FAIL | Người theo chuẩn ngôn ngữ của fixture | Reply không dấu. Thêm yêu cầu tiếng Việt có dấu cho nội dung CS được sinh ra và ví dụ đối chiếu; xử lý riêng trường hợp trích nguyên văn khách. |
| HL-015 | PASS | FAIL | Người theo ledger trong note | Reply 55.000đ, ledger 40.000đ. Helpful phải xét độ đúng; đưa số tiền sang code grader FM-08, lời lịch sự không bù được sai tiền. |
| HL-016 | PASS | FAIL | Người theo ledger trong note | Xin lỗi dài nhưng báo 55.000đ thay vì 35.000đ. Rubric không thưởng độ dài/lặp xin lỗi; accuracy là điều kiện bắt buộc. |
| HL-020 | PASS | FAIL | Người theo ledger trong note | Reply 90.000đ, ledger 120.000đ. Code phải bắt sai cả thiếu và thừa; kiểm số thực ghi thay vì proposal. |
| HL-028 | PASS | FAIL | Người theo ledger trong note | Reply 50.000đ, ledger 35.000đ; văn phong trau chuốt che sai tiền. Thêm cặp cùng nội dung sai tiền với reply ngắn/dài, kỳ vọng kết quả giống nhau. |
| HL-047 | PASS | FAIL | Người | “Ok bạn… rồi nhé” sai xưng hô theo fixture. Tách tone khỏi helpful tổng hợp; không cho phép criterion tổng bỏ qua lỗi tone đã quy định. |

## Rubric sau audit và bước áp dụng tiếp theo

1. Tone: lịch sự, xưng hô đúng bối cảnh, không ra lệnh/đùa không phù hợp; chấp nhận câu ngắn đủ ý, từ nghiệp vụ được cho phép và lỗi gõ nhỏ không đổi nghĩa. Không bắt buộc xin lỗi trong mọi tình huống.
2. Accuracy/safety: số tiền trong reply phải khớp ledger mới ghi; kết quả denial, approval và claim scope phải đúng. Chấm bằng code ở M3, không giao quyền quyết định tiền cho judge ngôn ngữ.
3. Helpfulness: xét xử lý đúng nhu cầu và hướng dẫn bước tiếp theo; không dùng độ dài, lời xin lỗi hoặc lời cảm ơn làm đại diện cho tính hữu ích. Chưa đưa judge helpful hiện tại vào gate.
4. Nhãn bất thường như H-081 cần hai lượt xem xét theo ticket/ledger và ghi version/changelog nếu sửa. Sau sửa rubric hoặc nhãn, phải chạy lại judge trên tập mới; replay hiện tại cố định nên tài liệu này không khẳng định các sửa đổi đã cải thiện metric.

## Tái lập và giới hạn

Chạy từ src/:

```powershell
.\.venv\Scripts\python.exe -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
# Kỳ vọng PASS floors, exit 0.
.\.venv\Scripts\python.exe -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
# Kỳ vọng FAIL floors, exit 1: đây là kết luận đúng của M2.
.\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= -p no:cacheprovider tests/test_lab9_stats.py tests/test_lab9_m2_calibration.py -k 'not paired_bootstrap'
```

15 test M2 PASS; 2 test paired_bootstrap thuộc M4 được loại khỏi lượt kiểm M2, hàm M4 chưa triển khai. Runtime Python 3.14.10 tại máy setup; số liệu được đo trên môi trường này.

Hai bộ đều 100 dòng replay công khai, không gọi LLM/API, không có held-out độc lập. Cần nhãn người mới, thêm trường hợp khó và bối cảnh ticket/ledger để kiểm tra ngoại suy. H-081 cho thấy nhãn người cũng có thể sai; ma trận hiện tại tính nguyên nhãn gốc để so đúng mốc bài lab.
