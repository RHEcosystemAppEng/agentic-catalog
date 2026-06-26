"""
Attach ABEvalFlow report summaries to catalog skills at site build time.

Reads eval/<pack>/<skill_name>/report.json (latest only; not collection.yaml).
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Match generate_collection_pages.py and app.js repository URL
GITHUB_BLOB_BASE = "https://github.com/RHEcosystemAppEng/agentic-collections/blob/main"

PASS_RECOMMENDATION = "pass"


def _github_blob_url(rel_path: str) -> str:
    rel = rel_path.lstrip("/")
    return f"{GITHUB_BLOB_BASE}/{rel}"


def _parse_iso_max(a: str, b: str) -> str:
    try:
        da = datetime.fromisoformat(a.replace("Z", "+00:00"))
        db = datetime.fromisoformat(b.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return a if a >= b else b
    return a if da >= db else b


def _iso_to_datetime(iso_value: str) -> Optional[datetime]:
    """Best-effort ISO timestamp parser for generated_at comparisons."""
    try:
        return datetime.fromisoformat(str(iso_value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def _confidence_fields(n_treatment: int, n_control: int) -> Dict[str, str]:
    n = min(n_treatment, n_control)
    if n >= 20:
        return {
            "confidence_level": "HIGH",
            "confidence_reason": f"{n} trials; strong signal strength",
        }
    if n >= 5:
        return {
            "confidence_level": "MEDIUM",
            "confidence_reason": f"{n} trials; acceptable but can be improved",
        }
    return {
        "confidence_level": "LOW",
        "confidence_reason": f"Only {n} trial{'s' if n != 1 else ''}; recommended minimum is 5",
    }


def _coverage_fields(n_treatment: int) -> Dict[str, str]:
    if n_treatment <= 0:
        return {"coverage_status": "NONE", "coverage_label": "Coverage: not evaluated"}
    if n_treatment < 5:
        return {"coverage_status": "PARTIAL", "coverage_label": f"Coverage: PARTIAL ({n_treatment} scenario{'s' if n_treatment != 1 else ''} tested)"}
    if n_treatment < 20:
        return {"coverage_status": "MODERATE", "coverage_label": f"Coverage: MODERATE ({n_treatment} scenarios tested)"}
    return {"coverage_status": "STRONG", "coverage_label": f"Coverage: STRONG ({n_treatment} scenarios tested)"}


def load_eval_report(
    root: Path, pack_name: str, skill_name: str
) -> Optional[Dict[str, Any]]:
    """
    Load and normalize eval/rh-sre/remediation/report.json-style content.
    Returns None if file missing or invalid.
    """
    base = root / "eval" / pack_name / skill_name
    report_json = base / "report.json"
    if not report_json.is_file():
        return None
    try:
        raw = json.loads(report_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    summary = raw.get("summary") or {}
    treat = summary.get("treatment") or {}
    ctrl = summary.get("control") or {}
    prov = raw.get("provenance") or {}
    trials = raw.get("trials") or {}
    treatment_trials = trials.get("treatment") or []

    n_trials_t = _safe_int(treat.get("n_trials"))
    n_trials_c = _safe_int(ctrl.get("n_trials"))
    n_failed_t = _safe_int(treat.get("n_failed"))

    conf = _confidence_fields(n_trials_t, n_trials_c)
    cov = _coverage_fields(n_trials_t)
    latest_trial = treatment_trials[-1] if treatment_trials else {}
    latest_trial_name = latest_trial.get("trial_name") if isinstance(latest_trial, dict) else None
    latest_trial_passed = latest_trial.get("passed") if isinstance(latest_trial, dict) else None
    latest_trial_reward = latest_trial.get("reward") if isinstance(latest_trial, dict) else None

    rel_json = f"eval/{pack_name}/{skill_name}/report.json"
    has_md = (root / "eval" / pack_name / skill_name / "report.md").is_file()

    out: Dict[str, Any] = {
        "recommendation": str(summary.get("recommendation", "")).lower() or None,
        "llm": summary.get("llm"),
        "related_pr": summary.get("related_pr"),
        "mean_reward_gap": summary.get("mean_reward_gap"),
        "mean_reward_treatment": treat.get("mean_reward"),
        "mean_reward_control": ctrl.get("mean_reward"),
        "pass_rate_treatment": treat.get("pass_rate"),
        "pass_rate_control": ctrl.get("pass_rate"),
        "n_trials_treatment": treat.get("n_trials"),
        "n_trials_control": ctrl.get("n_trials"),
        "n_passed_treatment": treat.get("n_passed"),
        "n_passed_control": ctrl.get("n_passed"),
        "n_failed_treatment": treat.get("n_failed"),
        "n_failed_control": ctrl.get("n_failed"),
        "fisher_p_value": summary.get("fisher_p_value"),
        "ttest_p_value": summary.get("ttest_p_value"),
        "generated_at": prov.get("generated_at"),
        "commit_sha": prov.get("commit_sha"),
        "pipeline_run_id": prov.get("pipeline_run_id"),
        "report_json_path": rel_json,
        "has_report_md": has_md,
        "scenarios_tested": n_trials_t,
        "failed_trials": n_failed_t,
        "has_failures": n_failed_t > 0,
        "latest_trial_name": latest_trial_name,
        "latest_trial_passed": latest_trial_passed,
        "latest_trial_reward": latest_trial_reward,
        **conf,
        **cov,
    }
    out["report_json_url"] = _github_blob_url(rel_json)
    out["report_dir_url"] = _github_blob_url(f"eval/{pack_name}/{skill_name}")
    if has_md:
        rel_md = f"eval/{pack_name}/{skill_name}/report.md"
        out["report_md_path"] = rel_md
        out["report_md_url"] = _github_blob_url(rel_md)
    else:
        out["report_md_path"] = None
        out["report_md_url"] = None

    return out


def _iter_catalog_skills(collection: Dict[str, Any]) -> List[Dict[str, Any]]:
    contents = collection.get("contents") or {}
    out: List[Dict[str, Any]] = []
    for key in ("orchestration_skills", "skills"):
        for s in contents.get(key) or []:
            if isinstance(s, dict):
                out.append(s)
    return out


def _rollup_from_evaluations(
    evals: List[Optional[Dict[str, Any]]], catalog_skill_count: int
) -> Dict[str, Any]:
    if catalog_skill_count == 0:
        return {
            "catalog_skill_count": 0,
            "evaluated_count": 0,
            "passed_count": 0,
            "failed_count": 0,
            "pass_rate": None,
            "median_uplift": None,
            "latest_generated_at": None,
            "coverage_label": "0/0 skills evaluated",
            "latest_pipeline_run_id": None,
            "latest_report_json_url": None,
            "latest_report_md_url": None,
            "latest_mean_reward_treatment": None,
            "latest_mean_reward_control": None,
            "coverage_pct": 0.0,
            "coverage_state": "NONE",
            "confidence_level": "NONE",
            "confidence_label": "NO DATA",
            "verified_execution_count": 0,
            "total_trials_treatment": 0,
            "trust_summary": "No evaluation data",
            "requires_more_evaluation": True,
        }

    evaluated = [e for e in evals if e is not None]
    n_eval = len(evaluated)
    passed = sum(
        1
        for e in evaluated
        if e.get("recommendation") == PASS_RECOMMENDATION
    )
    failed = max(n_eval - passed, 0)
    pass_rate = (passed / n_eval) if n_eval > 0 else None

    # ABEvalFlow no longer emits `uplift`; use mean_reward_gap as uplift proxy.
    uplifts = [
        float(e["mean_reward_gap"])
        for e in evaluated
        if e.get("mean_reward_gap") is not None
        and isinstance(e["mean_reward_gap"], (int, float))
    ]
    median_uplift = statistics.median(uplifts) if uplifts else None

    dates = [e["generated_at"] for e in evaluated if e.get("generated_at")]
    latest = None
    if dates:
        latest = dates[0]
        for d in dates[1:]:
            latest = _parse_iso_max(str(latest), str(d))

    latest_eval: Optional[Dict[str, Any]] = None
    for ev in evaluated:
        if latest_eval is None:
            latest_eval = ev
            continue
        current_dt = _iso_to_datetime(str(ev.get("generated_at")))
        latest_dt = _iso_to_datetime(str(latest_eval.get("generated_at")))
        if current_dt and latest_dt:
            if current_dt >= latest_dt:
                latest_eval = ev
        elif str(ev.get("generated_at") or "") >= str(latest_eval.get("generated_at") or ""):
            latest_eval = ev

    coverage_label = f"{n_eval}/{catalog_skill_count} skills evaluated"
    coverage_pct = (n_eval / catalog_skill_count * 100.0) if catalog_skill_count > 0 else 0.0
    if coverage_pct >= 95:
        coverage_state = "FULL"
    elif coverage_pct >= 50:
        coverage_state = "PARTIAL"
    elif coverage_pct > 0:
        coverage_state = "LOW"
    else:
        coverage_state = "NONE"

    total_trials_treatment = sum(
        _safe_int(e.get("n_trials_treatment")) for e in evaluated
    )
    verified_execution_count = total_trials_treatment
    if total_trials_treatment >= 20:
        confidence_level = "HIGH"
    elif total_trials_treatment >= 5:
        confidence_level = "MEDIUM"
    elif total_trials_treatment > 0:
        confidence_level = "LOW"
    else:
        confidence_level = "NONE"
    confidence_label = (
        "HIGH CONFIDENCE"
        if confidence_level == "HIGH"
        else ("MEDIUM CONFIDENCE" if confidence_level == "MEDIUM" else ("LOW CONFIDENCE" if confidence_level == "LOW" else "NO DATA"))
    )
    requires_more_evaluation = coverage_pct < 50.0 or total_trials_treatment < 5
    trust_summary = (
        f"Based on {total_trials_treatment} trial{'s' if total_trials_treatment != 1 else ''} · {coverage_state.lower()} coverage"
        if total_trials_treatment > 0
        else "No evaluation data"
    )

    return {
        "catalog_skill_count": catalog_skill_count,
        "evaluated_count": n_eval,
        "passed_count": passed,
        "failed_count": failed,
        "pass_rate": pass_rate,
        "median_uplift": median_uplift,
        "latest_generated_at": latest,
        "coverage_label": coverage_label,
        "latest_pipeline_run_id": latest_eval.get("pipeline_run_id") if latest_eval else None,
        "latest_report_json_url": latest_eval.get("report_json_url") if latest_eval else None,
        "latest_report_md_url": latest_eval.get("report_md_url") if latest_eval else None,
        "latest_mean_reward_treatment": latest_eval.get("mean_reward_treatment") if latest_eval else None,
        "latest_mean_reward_control": latest_eval.get("mean_reward_control") if latest_eval else None,
        "coverage_pct": round(coverage_pct, 1),
        "coverage_state": coverage_state,
        "confidence_level": confidence_level,
        "confidence_label": confidence_label,
        "verified_execution_count": verified_execution_count,
        "total_trials_treatment": total_trials_treatment,
        "trust_summary": trust_summary,
        "requires_more_evaluation": requires_more_evaluation,
    }


def apply_eval_enrichment(packs: List[Dict[str, Any]], root: Path) -> None:
    """
    Mutate each pack: attach skill['evaluation'] for catalog-listed skills when
    eval/<pack>/<skill>/report.json exists; set pack['evaluation_summary'] rollup.
    """
    root = root.resolve()
    for pack in packs:
        coll = pack.get("collection")
        if not isinstance(coll, dict):
            continue

        skills_ref = _iter_catalog_skills(coll)
        catalog_skill_count = len(skills_ref)
        attached: List[Optional[Dict[str, Any]]] = []

        pack_name = pack.get("name") or ""
        for skill in skills_ref:
            name = skill.get("name")
            if not name or not isinstance(name, str):
                attached.append(None)
                continue
            ev = load_eval_report(root, pack_name, name)
            if ev:
                ev["catalog_skill_count"] = catalog_skill_count
                skill["evaluation"] = ev
                attached.append(ev)
            else:
                attached.append(None)

        pack["evaluation_summary"] = _rollup_from_evaluations(attached, catalog_skill_count)


def _self_test() -> None:
    """Quick sanity check (run: python eval_site_enrichment.py)."""
    import tempfile

    sample = {
        "submission_name": "x",
        "provenance": {
            "generated_at": "2026-05-05T06:42:31.793527Z",
            "commit_sha": "abc",
            "pipeline_run_id": "run1",
        },
        "summary": {
            "treatment": {"n_trials": 5},
            "control": {"n_trials": 5},
            "mean_reward_gap": 0.05,
            "ttest_p_value": None,
            "fisher_p_value": 0.04,
            "recommendation": "pass",
        },
    }
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        p = root / "eval" / "rh-sre" / "remediation"
        p.mkdir(parents=True)
        (p / "report.json").write_text(json.dumps(sample), encoding="utf-8")
        (p / "report.md").write_text("# ok", encoding="utf-8")

        ev = load_eval_report(root, "rh-sre", "remediation")
        assert ev is not None
        assert ev["mean_reward_gap"] == 0.05
        assert ev["has_report_md"] is True

        pack = {
            "name": "rh-sre",
            "collection": {
                "contents": {
                    "skills": [{"name": "remediation", "description": "d"}],
                    "orchestration_skills": [],
                }
            },
        }
        apply_eval_enrichment([pack], root)
        assert pack["evaluation_summary"]["evaluated_count"] == 1
        assert pack["evaluation_summary"]["passed_count"] == 1
    print("eval_site_enrichment self-test OK")


if __name__ == "__main__":
    _self_test()
