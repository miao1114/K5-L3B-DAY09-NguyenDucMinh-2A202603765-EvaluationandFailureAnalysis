"""Update the evaluation handoff from generated M5-M7 evidence, preserving Core tables."""
from __future__ import annotations

import json
from pathlib import Path

from lab9.eval import load_spec


def main() -> None:
    docs = Path("../docs")
    evidence = json.loads((docs / "m67_evidence.json").read_text(encoding="utf-8"))
    spec = load_spec(Path("config/metric_spec_v2.yaml"))
    baseline = json.loads(Path("reports/baseline_v2.json").read_text(encoding="utf-8"))
    card = (docs / "eval_card.md").read_text(encoding="utf-8-sig").split("## V2 —", 1)[0]
    card = card.replace("M5–M7 chưa hoàn thành: slice gate, pass@k/pass^k, integrity và ratchet vẫn còn TODO.",
                        "M5–M7 đã triển khai và kiểm tra bằng vector public; bằng chứng v2 và giới hạn ở mục dưới.")
    metrics = "\n".join(f"| {m['id']} | `{json.dumps(m.get('threshold', {}))}` | {m.get('blocking', False)} | {baseline['metrics'][m['id']]} |" for m in spec["metrics"])
    aa = "\n".join(f"| {mid} | {delta:+.4f} |" for mid, delta in evidence["aa"]["delta"].items())
    scorecard = "\n".join(f"| {row['shape']} | {row['expected']} | {', '.join(row['blocked']) or 'none'} |" for row in evidence["scorecard"])
    v2 = f"""## V2 — M5, M6 và M7

Sinh bằng scripts.verify_m5, scripts.verify_m67 và scripts.build_advanced_docs. Chi tiết: [m5_validation.md](m5_validation.md), [m67_validation.md](m67_validation.md), [m67_cli.txt](m67_cli.txt).

Eval set v2 có {baseline['manifest']['items']} item × {len(baseline['manifest']['seeds'])} seed, SHA `{evidence['eval_set_sha']}`; baseline `{evidence['baseline_run_id']}`, metric spec {spec['metric_spec_version']}. Giữ nguyên item/nhãn/threshold và report v1. Code/grader là commit chứa thay đổi M6/M7; xem `git log -1 --format=%H -- src/lab9/stats.py src/lab9/integrity.py`.

| Metric | Threshold | Blocking | Baseline |
|---|---|---|---|
{metrics}

Slice money_movement min=0,95, adversarial min=0,90, denial min=0,90; tất cả blocking và có paired CI theo trung bình từng item. Slice_regression có pass_rate tổng 0,9357, Δ −0,043, CI [−0,121; +0,029], chỉ money_movement chặn vì pass_rate slice=0,85. Các ngưỡng M5 giữ nguyên; M6 chỉ bổ sung pass_hat_5 blocking ở spec 2.1.

### M6: A/A và độ ổn định

Seed chuẩn {evidence['aa']['reference_seeds']}; seed đối chứng {evidence['aa']['alternate_seeds']}. Dải nhiễu MockLLM quan sát bằng 0; baseline pass^5={evidence['pass_hat_5_baseline']}, sàn 0,85 thấp hơn baseline 0,0429. Flaky pass^5={evidence['pass_hat_5_flaky']} bị chặn. Không chọn sàn bằng cách hạ ngưỡng cho tới khi bắt được một variant cụ thể.

| Metric | A/A Δ |
|---|---|
{aa}

Với LLM thật dải nhiễu có thể >0 và cần A/A/held-out mới. Năm seed không bảo đảm phát hiện ổn định lỗi hiếm khoảng 1/3 seed hoặc hiếm hơn; cần nêu bất định/cỡ mẫu thay vì chỉnh ngưỡng để làm đẹp báo cáo.

### M7: scorecard và integrity

| Shape | Kỳ vọng | Metric chặn |
|---|---|---|
{scorecard}

Mutation 3/3, không báo nhầm fixed/honest_refactor; baseline tự so vẫn qua. Bốn trap public đều exit 1 vì INTEGRITY/ratchet. Hai kiểm tra bổ sung (dòng trùng trên report xanh, evaluator_failures trên report xanh) cũng bị chặn. Diagnostic quiet_fact_probe không có override event (db_fact_kept=1) vẫn bị chặn qua ledger/proposal; không sửa variant/trap được cung cấp.

CI lấy base spec từ checkout độc lập của commit base. Ratchet giữa các PR áp dụng sau khi baseline v2 đầu tiên đã được publish trên base branch; bản Core-only trước đó chỉ có spec v2 dự thảo. Các trap vẫn luôn kiểm ratchet với --base-spec. Không sửa report hoặc nới ngưỡng để qua gate.

### Giới hạn và release

MockLLM, tập public 28 item, 5 seed và judge replay không thay thế thử nghiệm production hoặc bộ chấm ẩn. Baseline swarm không có reply event nên không chứng minh chất lượng reply; FM-08 được kiểm bằng các trial có reply. Gate kiểm tính nhất quán report, không xác thực chữ ký/nguồn gốc trace; vẫn cần baseline/code grader đáng tin và review. Không khẳng định đã qua vector ẩn.

Owner: Nguyễn Đức Minh. Chỉ chuyển PR #3 sang Ready for review khi Core, M5 và Advanced CI đều Success; không có waiver tự động. Đổi dữ liệu/nhãn phải tăng eval_set_version, đổi metric phải tăng metric_spec_version, và không nới policy trên cùng tập đã được đóng băng.
"""
    (docs / "eval_card.md").write_text(card.rstrip() + "\n\n" + v2, encoding="utf-8", newline="\n")
    prd = (docs / "PRD_v1.1.md").read_text(encoding="utf-8-sig").split("## Advanced M5–M7", 1)[0]
    prd = prd.replace("Integrity/ratchet và slice gate thuộc M5–M7 chưa triển khai.",
                      "Integrity/ratchet và slice gate đã triển khai; xem bằng chứng M5–M7 trong eval card.")
    prd = prd.replace("Chỉ merge PR starter/d09 → main trong fork sau khi job eval-gate xanh.",
                      "Chỉ merge PR nhánh làm bài → main trong fork sau khi các job Core và Advanced cần thiết đều xanh.")
    prd += f"\n## Advanced M5–M7\n\nEval set v2 SHA {evidence['eval_set_sha']}; spec {spec['metric_spec_version']}. Gate bổ sung money_movement/adversarial slices, pass_hat_5≥0,85, kiểm integrity trước thống kê và ratchet so policy đã publish. Mutation public 3/3, 0 false alarm; 4/4 trap public và 2/2 kiểm tra bổ sung bị chặn. Chi tiết, A/A và giới hạn cỡ mẫu tại eval_card.md và m67_validation.md. Product approval vẫn chưa được xác nhận; kết quả public không phải bảo đảm điểm bộ chấm ẩn.\n"
    (docs / "PRD_v1.1.md").write_text(prd, encoding="utf-8", newline="\n")
    pr = f"""Complete Advanced M5–M7 so the gate catches localized regressions, intermittent failures, and corrupted evaluation evidence. Keep the 14-item v1 dataset and Core reports unchanged; v2 adds the supplied adversarial pack and frozen slice thresholds.

Implement pass@k/pass^k with invalid-input checks and choose blocking pass_hat_5>=0.85 after A/A delta=0 (baseline {evidence['pass_hat_5_baseline']}, flaky {evidence['pass_hat_5_flaky']}). Metric spec 2.1 adds this reliability guard without loosening M5 thresholds.

Integrity rejects duplicate/missing rows, changed seeds/slices, None/NaN/inf, evaluator failures, and aggregate values inconsistent with rows. Ratchet protects metric/slice thresholds, blocking, and no_significant_drop. CI checks the trusted base spec once the first v2 baseline is published. Supplied variants, traps, tests, Lab8 and the separate Day08 source remain unchanged.

Validation: 90 M1–M7 student tests pass locally. Mutation 3/3 regressions blocked, 0/2 false alarms; all 4 public traps plus 2 additional evidence checks rejected. Quiet fact corruption with no override event is blocked using outcomes. Reports/documents are script-generated. Hidden grading is not available.

| Shape | Expected | Blocked metrics |
|---|---|---|
{scorecard}

```text
pass_hat_5 baseline={evidence['pass_hat_5_baseline']} flaky={evidence['pass_hat_5_flaky']} floor=0.85
A/A: all metric deltas=0 for 11,22,33,44,55 vs 66,77,88,99,110
"""
    pr += "\n".join(f"{trap['name']}: exit 1 — INTEGRITY" for trap in evidence["public_traps"])
    pr += "\n```\n\nSee docs/m67_cli.txt for official mutation/A/A/trap CLI output and docs/m67_validation.md for detailed rejection reasons. Wait for all hosted CI jobs to pass before merging.\n"
    (docs / "pr_m5.md").write_text(pr, encoding="utf-8", newline="\n")
    print("updated eval_card.md, PRD_v1.1.md and PR #3 body")


if __name__ == "__main__":
    main()
