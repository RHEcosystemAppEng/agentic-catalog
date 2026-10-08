#!/usr/bin/env python3
"""Attach pack-level Soundcheck data from the Lola marketplace YAML.

P6 writes ``soundcheck_levels_summary`` (skill track) and ``mcp_evaluations[]``
(MCP scorecard) onto each module. Hub checkouts have no ``eval/`` tree, so this
is the only eval input for generate.

Do not join ``mcp_evaluations[].name`` onto hub ``mcp.json`` keys — Compass
entity names and Agent Plugins server keys differ. Keep two independent lists.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


EVALUATION_SOURCE = "soundcheck"


def _level_totals(summary: Any) -> tuple[int, int, int]:
    """Sum pass/fail/total across Soundcheck level buckets."""
    passed = failed = total = 0
    if not isinstance(summary, dict):
        return passed, failed, total
    for counts in summary.values():
        if not isinstance(counts, dict):
            continue
        passed += int(counts.get("pass") or 0)
        failed += int(counts.get("fail") or 0)
        total += int(counts.get("total") or 0)
    return passed, failed, total


def _latest_mcp_evaluated_at(mcp_evaluations: List[Dict[str, Any]]) -> Optional[str]:
    latest: Optional[str] = None
    for entry in mcp_evaluations:
        ts = entry.get("evaluated_at")
        if not isinstance(ts, str) or not ts.strip():
            continue
        if latest is None or ts > latest:
            latest = ts
    return latest


def build_evaluation_summary(
    soundcheck_levels_summary: Any,
    mcp_evaluations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Pack-level rollup from skill-track Soundcheck totals (not recommendation)."""
    passed, failed, total = _level_totals(soundcheck_levels_summary)
    evaluated_count = 1 if total > 0 else 0
    pass_rate = (passed / total) if total > 0 else None
    latest = _latest_mcp_evaluated_at(mcp_evaluations)
    return {
        "evaluation_source": EVALUATION_SOURCE,
        "passed_count": passed,
        "failed_count": failed,
        "total_checks": total,
        "evaluated_count": evaluated_count,
        "pass_rate": pass_rate,
        "latest_generated_at": latest,
        "mcp_evaluation_count": len(mcp_evaluations),
        "levels": dict(soundcheck_levels_summary)
        if isinstance(soundcheck_levels_summary, dict)
        else {},
    }


def apply_marketplace_eval(pack: Dict[str, Any], module: Dict[str, Any]) -> None:
    """Mutate *pack* with marketplace Soundcheck fields."""
    summary = module.get("soundcheck_levels_summary")
    raw_evals = module.get("mcp_evaluations")
    mcp_evaluations: List[Dict[str, Any]] = (
        [e for e in raw_evals if isinstance(e, dict)] if isinstance(raw_evals, list) else []
    )
    pack["soundcheck_levels_summary"] = summary if isinstance(summary, dict) else {}
    pack["mcp_evaluations"] = mcp_evaluations
    if module.get("content_hash"):
        pack["content_hash"] = module["content_hash"]
    pack["evaluation_summary"] = build_evaluation_summary(
        pack["soundcheck_levels_summary"],
        mcp_evaluations,
    )


def _self_test() -> None:
    summary = {
        "Foundational": {"pass": 17, "fail": 2, "total": 19},
        "Trusted": {"pass": 9, "fail": 0, "total": 9},
        "Certified": {"pass": 14, "fail": 4, "total": 18},
    }
    evals = [
        {
            "name": "assisted-installer",
            "entity_ref": "mcpserver:ai5-marketplace/assisted-installer",
            "evaluated_at": "2026-10-08T07:53:43.067768Z",
            "soundcheck_levels_summary": {
                "Lead": {"pass": 0, "fail": 1, "total": 1},
            },
        }
    ]
    pack: Dict[str, Any] = {"name": "rh-sre"}
    apply_marketplace_eval(
        pack,
        {"soundcheck_levels_summary": summary, "mcp_evaluations": evals,
         "content_hash": "sha256:abc"},
    )
    es = pack["evaluation_summary"]
    assert es["evaluation_source"] == EVALUATION_SOURCE
    assert es["passed_count"] == 40
    assert es["failed_count"] == 6
    assert es["total_checks"] == 46
    assert es["evaluated_count"] == 1
    assert pack["mcp_evaluations"][0]["name"] == "assisted-installer"
    assert pack["content_hash"] == "sha256:abc"

    empty: Dict[str, Any] = {"name": "ocp-admin"}
    apply_marketplace_eval(empty, {"mcp_evaluations": evals})
    assert empty["evaluation_summary"]["evaluated_count"] == 0
    assert empty["evaluation_summary"]["mcp_evaluation_count"] == 1
    print("marketplace_eval_enrichment self-test OK")


if __name__ == "__main__":
    _self_test()
