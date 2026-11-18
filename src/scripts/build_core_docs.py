"""Generate Core handoff documents from actual reports/spec, never edit report values.

Run from src/: python -m scripts.build_core_docs
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from lab9.eval import load_spec, per_item
from lab9.stats import paired_bootstrap


def main() -> None:
    docs = Path("../docs")
    spec = load_spec()
    reports = {name: json.loads(Path(f"reports/{file}.json").read_text(encoding="utf-8")) for name, file in
               (("baseline", "baseline_v1"), ("swarm", "eval_pr"), ("fixed", "eval_fixed"),
                ("seeded_regression", "eval_seeded_regression"))}
    base = reports["baseline"]
    metric_rows, ci_rows, gate_logs = [], [], []
    for metric in spec["metrics"]:
        mid = metric["id"]
        metric_rows.append(f"| {mid} | `{json.dumps(metric.get('threshold', {}))}` | {metric.get('blocking', False)} | {base['metrics'][mid]} |")
    for name in ("swarm", "fixed", "seeded_regression"):
        report = reports[name]
        for metric in spec["metrics"]:
            mid = metric["id"]
            if not metric.get("threshold", {}).get("no_significant_drop"):
                continue
            a, b = per_item(report, mid), per_item(base, mid)
            keys = sorted(a)
            if set(a) != set(b):
                raise ValueError("paired items differ")
            delta, low, high = paired_bootstrap(
                [a[k] for k in keys], [b[k] for k in keys],
                n_resamples=spec["bootstrap"]["n_resamples"], rng=spec["bootstrap"]["rng"],
                confidence=spec["bootstrap"]["confidence"],
            )
            ci_rows.append(f"| {name} | {mid} | {report['metrics'][mid]} | {delta:+.3f} | [{low:+.3f}, {high:+.3f}] |")
        result = subprocess.run(
            [sys.executable, "-m", "lab9.gate", "--pr", f"reports/eval_{'pr' if name == 'swarm' else name}.json",
             "--baseline", "reports/baseline_v1.json", "--spec", "config/metric_spec.yaml"],
            capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"},
        )
        expected = 1 if name == "seeded_regression" else 0
        if result.returncode != expected or (expected == 1 and "pass_rate" not in result.stdout.split("exit 1 — blocked:")[-1]):
            raise RuntimeError(f"unexpected gate decision for {name}: {result.stdout} {result.stderr}")
        gate_logs.append(f"### {name}: exit {result.returncode}\n\n```text\n{result.stdout.strip()}\n```\n")
    metrics = "\n".join(metric_rows)
    cis = "\n".join(ci_rows)
    runs = "\n".join(f"- {name}: `{report['run_id']}`" for name, report in reports.items())
    source_commit = "Cùng commit thay đổi mã nguồn đi kèm tài liệu; tra bằng `git log -1 --format=%H -- src/lab9/stats.py src/lab9/graders.py`."
    card = f"""# Eval card — LogiX-VN refund agent, Core v1

Sinh từ report/spec bằng `python -m scripts.build_core_docs` tại src/; không sửa số liệu report bằng tay.

## Phiên bản và run ID

{source_commit}

Eval set v1, SHA `{base['manifest']['eval_set_sha']}`, {base['manifest']['items']} item × {len(base['manifest']['seeds'])} seed {base['manifest']['seeds']}, nhãn tách riêng tại labels_v1.json; nguồn lab8_public. Metric spec {spec['metric_spec_version']}; runtime Python {base['manifest']['python']}, {base['manifest']['llm']}.

{runs}

## Metric và ngưỡng

| Metric | Threshold | Blocking | Baseline |
|---|---|---|---|
{metrics}

## So sánh paired trên trung bình từng item

Đơn vị resample là 14 item, không phải 70 trial độc lập. Percentile paired bootstrap, {spec['bootstrap']['n_resamples']} resamples, RNG {spec['bootstrap']['rng']}, confidence {spec['bootstrap']['confidence']}; Δ = PR − baseline.

| Shape | Metric | Giá trị | Δ | CI |
|---|---|---|---|---|
{cis}

Swarm tự so baseline và fixed đều exit 0. Seeded_regression exit 1, có pass_rate trong danh sách bị chặn. Xem [m4_validation.md](m4_validation.md) để đọc output thực tế.

## Judge, trace và phạm vi sử dụng

Tone κ=0,757, precision=0,857, recall=0,800: đạt calibration replay; helpful κ=0,375, recall=0,300 nên bị loại. Xem [judge_audit.md](judge_audit.md), [failure_taxonomy.md](failure_taxonomy.md) và [trace_case.md](trace_case.md). Detection M3=100%, false alarm fixed=0% theo public variants.

Eval owner: Nguyễn Đức Minh. Khi gate exit 1, owner kiểm tra trace, sửa implementation, sinh lại report và chạy gate; không sửa report hoặc hạ ngưỡng. Không merge khi CI đỏ.

Pilot chỉ là mô phỏng offline các claim hoàn phí giao trễ/hàng hỏng, theo policy và approval trong fixture; không chuyển tiền thật, không hỗ trợ quyết định tranh chấp pháp lý/nhiều đơn ngoài fixture.

## Giới hạn và tăng phiên bản

MockLLM không đại diện model thật; 14 item có CI rộng; judge replay công khai không phải held-out. Swarm gốc không phát reply event, nên metric reply_amount_correct=1 ở baseline chỉ có nghĩa không quan sát thấy khẳng định tiền bằng text để chấm; đối chứng FM-08 đã thử riêng trên shape có reply. Chưa có dữ liệu người dùng thật. Chi phí chỉ là mô phỏng từ pricing.yaml.

M5–M7 chưa hoàn thành: slice gate, pass@k/pass^k, integrity và ratchet vẫn còn TODO. Đổi tập item/nhãn phải tăng eval_set_version và sinh baseline mới; đổi metric/ngưỡng phải tăng metric_spec_version, ghi lý do và không nới ngưỡng trên cùng eval set. CI GitHub cần được xác nhận từ PR thực tế; kết quả cục bộ không phải bằng chứng job hosted đã xanh.
"""
    prd = f"""# PRD v1.1 — LogiX-VN refund agent

v1.1 giữ phạm vi chức năng Day08 và bổ sung tiêu chí đánh giá/release. Sinh bảng số liệu từ report/spec bằng scripts.build_core_docs.

## Phạm vi và owner

Mô phỏng offline hoàn phí giao trễ/hàng hỏng trong 14 claim public, theo cap và approval trong fixture; không API/model thật, không chuyển tiền thật, không xử lý tranh chấp pháp lý hoặc claim nhiều đơn ngoài fixture. Eval owner: Nguyễn Đức Minh; Product approval: chưa được xác nhận.

## Định nghĩa chạy đúng

Baseline `{base['run_id']}`, eval set SHA `{base['manifest']['eval_set_sha']}`. {source_commit}

| Metric | Threshold | Chặn release | Baseline |
|---|---|---|---|
{metrics}

Giảm có ý nghĩa: CI 95% paired bootstrap của Δ(PR−baseline) nằm hoàn toàn dưới 0; resample trung bình theo item với cùng seed, percentile, RNG 2027, 1000 resamples. Cả floor tuyệt đối và kiểm giảm có ý nghĩa đều được áp dụng.

## Failure mode → grader

| FM | Grader / kiểm tra | Loại và lý do |
|---|---|---|
| FM-01 | SecretLeak | Code dò forbidden data trong artifact. |
| FM-02 | TrialPass + ReplyAmountCorrect | Code kiểm status và lời báo hoàn tiền khi ledger không ghi; ApprovalBypass chỉ bắt tác động trái phép. |
| FM-03 | DbFactKept + RefundAmountCorrect + ProposalAmountCorrect | Code đối chiếu fact/event, proposal và ledger. |
| FM-04 | RefundAmountCorrect + ProposalAmountCorrect | Code kiểm tiền và công thức qua nhãn. |
| FM-05 | ProposalAmountCorrect + RefundAmountCorrect | Code bắt trừ lịch sử hai lần, cả khi ledger vẫn bằng 0. |
| FM-06 | TrialPass + RefundAmountCorrect + ProposalAmountCorrect | Code phát hiện sai outcome/proposal; kiểm provenance điều khoản bằng trace review. |
| FM-07 | ApprovalBypass | Code kiểm unexpected ledger rows. |
| FM-08 | ReplyAmountCorrect | Code so số tiền reply với ledger mới ghi. |

Judge chỉ dùng tone trong phạm vi đã calibration; helpful bị loại. Tiền, approval và scope luôn dùng code. Xem judge_audit.md và m3_trajectory.md để biết giới hạn.

## Cổng release và bằng chứng

Lệnh: `python -m lab9.gate --pr reports/eval_<shape>.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml` từ src/.

Swarm và fixed phải exit 0; seeded_regression phải exit 1 với pass_rate bị chặn. Baseline từ swarm trên cùng tập item/seed, do script sinh và commit cùng nhánh; CI ci_check so với swarm chạy mới để kiểm tính tái lập. Sau merge, baseline nằm trên main của fork.

Owner xử lý gate đỏ bằng sửa lỗi, chạy test, sinh lại report. Không có waiver tự động; ngoại lệ cần Product phê duyệt rõ trong PR trước khi đổi chính sách release. Chưa có phê duyệt hoặc waiver nào được ghi nhận. M4 local pass chưa tương đương hosted CI xanh.

## Rủi ro mở và thay đổi phiên bản

MockLLM, 14 item, judge replay công khai, không có dữ liệu người dùng thật; baseline swarm không có reply event. Không kết luận chất lượng production hoặc độ đúng reply từ baseline này. Integrity/ratchet và slice gate thuộc M5–M7 chưa triển khai.

Thêm/sửa item hoặc nhãn: tăng eval_set_version, sinh baseline mới. Đổi metric/ngưỡng: tăng metric_spec_version và giải thích; không nới ngưỡng trên cùng eval set. Chỉ merge PR starter/d09 → main trong fork sau khi job eval-gate xanh. Hạn nộp theo LMS của ca, chưa ghi nhận ngày giờ cụ thể ở tài liệu này.
"""
    validation = "# M4 — Gate validation cục bộ\n\nSinh bằng scripts.build_core_docs từ gate CLI và report thực tế. Không phải log GitHub Actions.\n\n" + "\n".join(gate_logs)
    validation += "\nKiểm tra Core: 46 test PASS; smoke M0 PASS; evalset 0 problem(s); ci_check exit 0. M5–M7 không nằm trong lượt kiểm này.\n"
    pr = """Swarm đã chạy được nhưng cần bộ đánh giá để chặn regression trước khi merge. PR hoàn thiện Core M1–M4: taxonomy/provenance, calibration và audit judge, trajectory graders (gồm so tiền reply với ledger), paired bootstrap và baseline v1.

Validation cục bộ: smoke PASS; evalset 0 problem(s); 46 test Core PASS; ci_check exit 0. Detection public variants 100%, false alarm fixed 0%. Swarm và fixed qua gate; seeded_regression bị chặn ở pass_rate với CI Δ khớp mốc bài lab. Mã nguồn Lab8 và src của dự án Day08 giữ nguyên. M5–M7 còn TODO.

Hosted job eval-gate cần được xác nhận trên PR này trước khi merge.\n\n""" + "\n".join(gate_logs)
    for name, body in (("eval_card.md", card), ("PRD_v1.1.md", prd), ("m4_validation.md", validation), ("pr_m4.md", pr)):
        (docs / name).write_text(body, encoding="utf-8")
        print(f"wrote {docs / name}")


if __name__ == "__main__":
    main()
