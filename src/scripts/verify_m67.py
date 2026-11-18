"""Reproduce M6/M7 reliability, A/A, mutation, and integrity evidence.

Run after scripts.verify_m5: python -m scripts.verify_m67
Reports are produced from fresh evaluations, never edited to change a verdict.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from lab8.console import utf8_stdio
from lab8.shapes import SHAPES
from lab9 import gate, traps, variants
from lab9.eval import load_spec, run_eval
from lab9.variant_agent import make_shape


def write_report(path: str, report: dict) -> None:
    if report["evaluator_failures"]:
        raise RuntimeError(report["evaluator_failures"])
    Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    utf8_stdio()
    spec = load_spec(Path("config/metric_spec_v2.yaml"))
    base = json.loads(Path("reports/baseline_v2.json").read_text(encoding="utf-8"))
    if gate.check(base, base, spec, spec)[0]:
        raise AssertionError("baseline must pass its own gate")
    variants.register()
    alternate = run_eval("swarm", spec, [66, 77, 88, 99, 110])
    write_report("reports/eval_v2_aa_alternate.json", alternate)
    delta = {mid: round(alternate["metrics"][mid] - value, 10) for mid, value in base["metrics"].items()
             if isinstance(value, (int, float)) and isinstance(alternate["metrics"].get(mid), (int, float))}
    if any(value != 0 for value in delta.values()):
        raise AssertionError(f"unexpected MockLLM A/A difference: {delta}")
    flaky = run_eval("flaky_regression", spec)
    write_report("reports/eval_v2_flaky_regression.json", flaky)
    blocked, flaky_lines = gate.check(flaky, base, spec, spec)
    if "pass_hat_5" not in blocked or "integrity" in blocked:
        raise AssertionError("flaky regression must be caught by the reliability floor")
    # An independent diagnostic uses the supplied quiet bug switch in memory only.
    SHAPES["quiet_fact_probe"] = make_shape("quiet_fact_probe", {"no_override", "quiet_override"})
    quiet = run_eval("quiet_fact_probe", spec)
    write_report("reports/eval_v2_quiet_fact_probe.json", quiet)
    quiet_blocked, quiet_lines = gate.check(quiet, base, spec, spec)
    if not quiet_blocked or "integrity" in quiet_blocked or quiet["metrics"]["db_fact_kept"] != 1.0:
        raise AssertionError("silent fact corruption must be detected from outcomes")
    variants_reports = {
        name: json.loads(Path(f"reports/eval_v2_{name}.json").read_text(encoding="utf-8"))
        for name in ("fixed", "honest_refactor", "seeded_regression", "slice_regression")
    }
    variants_reports["flaky_regression"] = flaky
    scorecard = []
    for name, report in variants_reports.items():
        blocked_ids, lines = gate.check(report, base, spec, spec)
        expected = name not in ("fixed", "honest_refactor")
        if bool(blocked_ids) != expected or "integrity" in blocked_ids:
            raise AssertionError(f"incorrect variant gate decision: {name}: {blocked_ids}")
        scorecard.append({"shape": name, "expected": "block" if expected else "merge",
                          "blocked": blocked_ids, "lines": lines, "run_id": report["run_id"]})
    slice_report = variants_reports["slice_regression"]
    public_traps = []
    for name, (report, loosened_spec) in traps.build(slice_report, spec).items():
        blocked_ids, lines = gate.check(report, base, loosened_spec or spec, spec if loosened_spec else None)
        if blocked_ids != ["integrity"]:
            raise AssertionError(f"trap did not fail integrity: {name}: {blocked_ids}")
        public_traps.append({"name": name, "exit_code": 1, "lines": lines})
    extra = {}
    duplicate = copy.deepcopy(base)
    duplicate["rows"][-1] = copy.deepcopy(duplicate["rows"][0])
    extra["duplicate_green_row"] = duplicate
    green_errors = copy.deepcopy(base)
    green_errors["evaluator_failures"] = ["diagnostic evaluator failure on an otherwise green report"]
    extra["green_evaluator_failure"] = green_errors
    extra_results = []
    for name, report in extra.items():
        blocked_ids, lines = gate.check(report, base, spec, spec)
        if blocked_ids != ["integrity"]:
            raise AssertionError(f"extra trap was not rejected: {name}")
        extra_results.append({"name": name, "exit_code": 1, "lines": lines})
    altered = copy.deepcopy(spec)
    altered["pass_k"] = []
    forged = copy.deepcopy(base)
    forged["metrics"]["pass_hat_5"] = 1.0
    blocked_ids, lines = gate.check(forged, base, altered, spec)
    if blocked_ids != ["integrity"] or not any("aggregate pass_hat_5 disagrees" in line for line in lines):
        raise AssertionError("deleted pass_k bypass was not independently rejected")
    extra_results.append({"name": "deleted_pass_k_forged_reliability", "exit_code": 1, "lines": lines})
    evidence = {"baseline_run_id": base["run_id"], "eval_set_sha": base["manifest"]["eval_set_sha"],
                "metric_spec_version": spec["metric_spec_version"],
                "aa": {"reference_seeds": base["manifest"]["seeds"], "alternate_seeds": alternate["manifest"]["seeds"],
                       "delta": delta}, "pass_hat_5_baseline": base["metrics"]["pass_hat_5"],
                "pass_hat_5_flaky": flaky["metrics"]["pass_hat_5"],
                "scorecard": scorecard, "public_traps": public_traps, "additional_checks": extra_results,
                "quiet_fact_probe": {"run_id": quiet["run_id"], "db_fact_kept": quiet["metrics"]["db_fact_kept"],
                                     "blocked": quiet_blocked, "lines": quiet_lines}}
    Path("../docs/m67_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = ["# M6/M7 — Reliability và integrity", "", "Sinh bằng `python -m scripts.verify_m67` từ src/.", "",
             f"Baseline `{base['run_id']}`, eval set SHA `{evidence['eval_set_sha']}`, spec {spec['metric_spec_version']}.", "",
             "## M6", "", "pass@k = 1 − C(n−c,k)/C(n,k); pass^k = C(c,k)/C(n,k). Từ chối n≤0, c ngoài [0,n], k ngoài [1,n], số không nguyên và boolean. Test đối chiếu phép liệt kê mọi mẫu nhỏ.", "",
             f"A/A: seeds {base['manifest']['seeds']} và {alternate['manifest']['seeds']}; mọi Δ = 0 trên MockLLM. Baseline pass^5={base['metrics']['pass_hat_5']}; sàn blocking=0,85, cách baseline 0,0429, nằm ngoài nhiễu quan sát bằng 0. Flaky pass^5={flaky['metrics']['pass_hat_5']} bị chặn.", "",
             "Với LLM thật, decoding, hạ tầng và judge có thể gây dải nhiễu >0; cần A/A độc lập và ngưỡng ngoài dải đó. Năm seed không bảo đảm bắt ổn định lỗi hiếm khoảng 1/3 seed hoặc hiếm hơn; không hạ ngưỡng theo từng variant để làm đẹp scorecard.", "",
             "## Mutation scorecard", "", "| Shape | Kỳ vọng | Metric chặn |", "|---|---|---|"]
    lines += [f"| {row['shape']} | {row['expected']} | {', '.join(row['blocked']) or 'none'} |" for row in scorecard]
    lines += ["", "Mutation score 3/3; false alarm 0/2. Baseline tự so chính nó qua gate. Quiet fact probe không phát override (db_fact_kept=1) vẫn bị chặn qua outcome/proposal; không sửa các variant được cung cấp.", "",
              "## M7", "", "Kiểm tra cả PR và baseline: đủ tích item×seed, không trùng, không thiếu/đổi seed, slice đúng dataset và nhất quán giữa seed; không NaN/inf hoặc score thiếu; evaluator_failures phải rỗng; recompute aggregate từ rows để bắt số tổng bị làm đẹp. Ratchet giữ min/max/max_increase, blocking, metric, slice và no_significant_drop khi dùng --base-spec trên cùng eval_set_version.", ""]
    for trap in public_traps + extra_results:
        lines += [f"### {trap['name']}: exit 1 — INTEGRITY", "", "```text", *trap["lines"], "```", ""]
    lines += ["## Tái lập", "", "```powershell", "python -m pytest -q -m student -o addopts= -k lab9",
              "python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110",
              "python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json",
              "python -m lab9.traps --pr reports/eval_v2_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml",
              "python -m scripts.verify_m67", "```", "",
              "Giới hạn: đây là vector public và các kiểm tra bổ sung tự xây, không phải bộ chấm ẩn. Gate không xác thực chữ ký/nguồn gốc trace; cần baseline và code grader do CI/reviewer tin cậy. --base-spec phải lấy từ nhánh gốc được bảo vệ, không tin một file tùy ý do PR đưa vào. Không khẳng định điểm rubric trước khi giảng viên chạy bộ ẩn."]
    Path("../docs/m67_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"M6/M7 PASS: A/A delta=0; mutation 3/3, false alarms=0; traps={len(public_traps)}/4; extra={len(extra_results)}/{len(extra_results)}", flush=True)


if __name__ == "__main__":
    main()
