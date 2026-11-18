"""Validate report evidence and spec ratchets before any statistical gate decision."""
from __future__ import annotations

from math import isclose, isfinite
from numbers import Real
from pathlib import Path

from lab9 import evalset
from lab9.eval import aggregate
from lab9.graders import GRADERS


def _number(value) -> bool:
    return isinstance(value, Real) and isfinite(value)


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    problems = []
    for group, identity in (("metrics", "id"), ("slices", "name")):
        old = {entry[identity]: entry for entry in base_spec.get(group, [])}
        new = {entry[identity]: entry for entry in spec.get(group, [])}
        if len(new) != len(spec.get(group, [])):
            problems.append(f"ratchet: duplicate {group} identifiers")
        for name, before in old.items():
            after = new.get(name)
            if after is None:
                problems.append(f"ratchet: removed {group} {name}")
                continue
            if before.get("blocking") and not after.get("blocking"):
                problems.append(f"ratchet: {name} is no longer blocking")
            if group == "slices" and before.get("metric") != after.get("metric"):
                problems.append(f"ratchet: {name} changed slice metric")
            if group == "metrics" and before.get("kind") != after.get("kind"):
                problems.append(f"ratchet: {name} changed metric kind")
            prior = before.get("threshold", {}) if group == "metrics" else before
            current = after.get("threshold", {}) if group == "metrics" else after
            for bound in ("min", "max", "max_increase"):
                if bound not in prior:
                    continue
                value = current.get(bound)
                if not _number(value) or isinstance(value, bool):
                    problems.append(f"ratchet: {name} removed/invalid {bound}")
                elif (bound == "min" and value < prior[bound]) or (bound != "min" and value > prior[bound]):
                    problems.append(f"ratchet: {name} loosened {bound}")
            if prior.get("no_significant_drop") and not current.get("no_significant_drop"):
                problems.append(f"ratchet: {name} removed no_significant_drop")
    return problems


def check_reports(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    problems = []
    if not isinstance(pr, dict) or not isinstance(base, dict):
        return ["report must be an object"]
    if base_spec is not None:
        problems.extend(_ratchet(spec, base_spec))
    rules = spec.get("metrics", [])
    metric_ids = [m["id"] for m in rules if m["id"] in GRADERS]
    required = {m["id"] for m in rules}
    blocking = {m["id"] for m in rules if m.get("blocking")}
    if len(required) != len(rules):
        problems.append("duplicate spec metric identifiers")
    slices = spec.get("slices", [])
    if len({s["name"] for s in slices}) != len(slices):
        problems.append("duplicate spec slice names")
    trusted_items = None
    if spec.get("eval_set"):
        try:
            path = Path(spec["eval_set"])
            data = evalset.load_jsonl(path)
            trusted_items = {item["item_id"]: tuple(sorted(item.get("slices", []))) for item in data}
            trusted_sha = evalset.sha12(path)
            if len(trusted_items) != len(data):
                problems.append("eval set contains duplicate item IDs")
        except (OSError, ValueError, KeyError, TypeError) as error:
            problems.append(f"cannot validate configured eval set: {error}")
    parsed = {}
    for name, report in (("PR", pr), ("baseline", base)):
        manifest, rows, metrics = report.get("manifest"), report.get("rows"), report.get("metrics")
        if not isinstance(manifest, dict) or not isinstance(rows, list) or not isinstance(metrics, dict):
            problems.append(f"{name}: malformed manifest/rows/metrics")
            continue
        failures = report.get("evaluator_failures")
        if not isinstance(failures, list) or failures:
            problems.append(f"{name}: evaluator_failures must be an empty list")
        sha = manifest.get("eval_set_sha")
        if not isinstance(sha, str) or not sha:
            problems.append(f"{name}: missing eval_set_sha")
        if trusted_items is not None and sha != trusted_sha:
            problems.append(f"{name}: eval_set_sha does not match configured dataset")
        if spec.get("metric_spec_version") is not None and manifest.get("metric_spec_version") != spec["metric_spec_version"]:
            problems.append(f"{name}: metric spec version differs; regenerate report")
        count, seeds = manifest.get("items"), manifest.get("seeds")
        valid_count = type(count) is int and count > 0
        valid_seeds = isinstance(seeds, list) and bool(seeds) and all(type(seed) is int for seed in seeds)
        if not valid_count or not valid_seeds:
            problems.append(f"{name}: invalid items/seeds manifest")
            continue
        if len(set(seeds)) != len(seeds):
            problems.append(f"{name}: duplicate manifest seeds")
        if spec.get("seeds") is not None and set(seeds) != set(spec["seeds"]):
            problems.append(f"{name}: manifest seeds differ from spec")
        if len(rows) != count * len(seeds):
            problems.append(f"{name}: row count differs from items x seeds")
        index, item_slices, row_errors = {}, {}, False
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("item_id"), str) or not row["item_id"] or type(row.get("seed")) is not int:
                problems.append(f"{name}: malformed item/seed row")
                row_errors = True
                continue
            if row["seed"] not in seeds:
                problems.append(f"{name}: row uses an undeclared seed")
            tags = row.get("slices", [])
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags) or len(set(tags)) != len(tags):
                problems.append(f"{name}: malformed slice tags")
                tags = []
            tags = tuple(sorted(tags))
            pair = (row["item_id"], row["seed"])
            if pair in index:
                problems.append(f"{name}: duplicate (item, seed) rows")
            index[pair] = {**row, "slices": list(tags)}
            if row["item_id"] in item_slices and item_slices[row["item_id"]] != tags:
                problems.append(f"{name}: slice tags vary across seeds")
            item_slices[row["item_id"]] = tags
            for mid in metric_ids:
                value = row.get(mid)
                if not _number(value) or value not in (0, 1):
                    problems.append(f"{name}: missing/nonfinite/invalid row metric {mid}")
                    row_errors = True
            if "cost" in row or "cost_per_success" in required or "cost_per_success" in metrics:
                if not _number(row.get("cost")) or row["cost"] < 0:
                    problems.append(f"{name}: missing/invalid row cost")
                    row_errors = True
        if len(item_slices) != count:
            problems.append(f"{name}: distinct item count differs from manifest")
        if set(index) != {(item, seed) for item in item_slices for seed in seeds}:
            problems.append(f"{name}: incomplete item x seed coverage")
        if trusted_items is not None and item_slices != trusted_items:
            problems.append(f"{name}: item IDs/slice tags differ from configured dataset")
        for mid in required - metrics.keys():
            problems.append(f"{name}: missing aggregate metric {mid}")
        for mid, value in metrics.items():
            if value is None and mid not in blocking:
                continue
            if not _number(value):
                problems.append(f"{name}: nonfinite/missing aggregate metric {mid}")
        if not row_errors and rows:
            normalized = [{**row, "cost": row.get("cost", 0.0)} for row in rows]
            recomputed = aggregate(normalized, metric_ids, k_values=spec.get("pass_k", []))
            for mid, expected in recomputed.items():
                if mid not in metrics:
                    continue
                actual = metrics[mid]
                if expected is None:
                    if actual is not None:
                        problems.append(f"{name}: aggregate {mid} disagrees with rows")
                elif not _number(actual) or not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9):
                    problems.append(f"{name}: aggregate {mid} disagrees with rows")
        parsed[name] = (manifest, index)
    if len(parsed) == 2:
        p_manifest, p_rows = parsed["PR"]
        b_manifest, b_rows = parsed["baseline"]
        if p_manifest.get("eval_set_sha") != b_manifest.get("eval_set_sha"):
            problems.append("PR/baseline eval_set_sha differs")
        if set(p_rows) != set(b_rows):
            problems.append("PR/baseline (item, seed) sets differ")
        for pair in p_rows.keys() & b_rows.keys():
            if sorted(p_rows[pair].get("slices", [])) != sorted(b_rows[pair].get("slices", [])):
                problems.append("PR/baseline slice tags differ")
    return list(dict.fromkeys(problems))
