"""CLI: python -m qc_reviewer review <file>"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import validator, defect_detector, rubric, report


def review_one(path: Path, rubric_path: Path | None, out_dir: Path) -> bool:
    try:
        scenario = validator.load_scenario(path)
    except ValueError as e:
        print(f"[ERROR] {path}: {e}", file=sys.stderr)
        return False

    structural = validator.validate_structure(scenario)
    semantic = defect_detector.detect_defects(scenario)
    defects = structural + semantic

    rubric_data = rubric.load_rubric(rubric_path) if rubric_path else rubric.load_rubric()
    score = rubric.score_scenario(rubric_data, defects)

    scenario_id = scenario.get("scenario_id", path.stem)
    md_path, json_path = report.write_reports(out_dir, scenario_id, str(path), defects, score)

    verdict = "PASS" if score["passed"] else "FAIL"
    print(f"{verdict}  {scenario_id:30s}  {score['overall_score']:5.1f}/100  defects={len(defects)}")
    return score["passed"]


def main(argv=None):
    p = argparse.ArgumentParser(prog="qc_reviewer")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review")
    r.add_argument("path", type=Path)
    r.add_argument("--rubric", type=Path, default=None)
    r.add_argument("--out", type=Path, default=Path("reports"))
    args = p.parse_args(argv)
    if args.cmd == "review":
        return 0 if review_one(args.path, args.rubric, args.out) else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
