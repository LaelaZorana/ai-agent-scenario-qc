"""CLI: python -m qc_reviewer review <file> | batch <dir>"""
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
    print(f"{verdict}  {scenario_id:30s}  {score['overall_score']:5.1f}/100  "
          f"defects={len(defects)}  -> {md_path}")
    return score["passed"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qc_reviewer", description="AI agent scenario QC reviewer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_rev = sub.add_parser("review", help="Review a single scenario file")
    p_rev.add_argument("path", type=Path)
    p_rev.add_argument("--rubric", type=Path, default=None)
    p_rev.add_argument("--out", type=Path, default=Path("reports"))

    p_bat = sub.add_parser("batch", help="Review every .json file in a directory")
    p_bat.add_argument("dir", type=Path)
    p_bat.add_argument("--rubric", type=Path, default=None)
    p_bat.add_argument("--out", type=Path, default=Path("reports"))

    args = parser.parse_args(argv)

    if args.cmd == "review":
        ok = review_one(args.path, args.rubric, args.out)
        return 0 if ok else 1

    if args.cmd == "batch":
        files = sorted(args.dir.glob("*.json"))
        if not files:
            print(f"No .json files in {args.dir}", file=sys.stderr)
            return 1
        passed = sum(review_one(f, args.rubric, args.out) for f in files)
        print(f"\nSummary: {passed}/{len(files)} scenarios passed.")
        return 0 if passed == len(files) else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
