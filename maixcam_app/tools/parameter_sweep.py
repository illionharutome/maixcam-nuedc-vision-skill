"""Deterministic grid search over nested visual YAML/JSON parameters."""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import statistics
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.main import load_config
from maixcam_app.tools.replay_test import evaluate_directory


def set_nested(config: dict, dotted_path: str, value) -> None:
    current = config
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    last = parts[-1]
    if isinstance(current, list):
        current[int(last)] = value
    else:
        current[last] = value


def main() -> None:
    parser = argparse.ArgumentParser(description="Grid-search YAML parameters against a fully labeled replay set")
    parser.add_argument("--base", required=True)
    parser.add_argument("--grid", required=True, help="JSON object: dotted.path -> list of values")
    parser.add_argument("--samples", required=True)
    parser.add_argument("--module", default="laser_spot")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--scoring-fps", type=float, default=0.0,
                        help="fixed MaixCAM FPS for every candidate; leave 0 for accuracy-only offline search")
    parser.add_argument("--max-combinations", type=int, default=256)
    parser.add_argument("--output", required=True)
    parser.add_argument("--save-best", action="store_true")
    args = parser.parse_args()

    base = load_config(args.base)
    grid = json.loads(Path(args.grid).read_text(encoding="utf-8"))
    if not isinstance(grid, dict) or not grid or any(not isinstance(values, list) or not values for values in grid.values()):
        raise ValueError("grid must be a non-empty object of dotted paths to non-empty value lists")
    paths = list(grid)
    combinations = list(itertools.product(*(grid[path] for path in paths)))
    if len(combinations) > args.max_combinations:
        raise ValueError(f"grid has {len(combinations)} combinations; limit is {args.max_combinations}")

    results = []
    best_config = None
    with tempfile.TemporaryDirectory(prefix="maixcam_sweep_") as temporary:
        candidate_path = Path(temporary) / "candidate.yaml"
        for index, values in enumerate(combinations, 1):
            candidate = copy.deepcopy(base)
            parameters = dict(zip(paths, values))
            for path, value in parameters.items():
                set_nested(candidate, path, value)
            candidate_path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            runs = [evaluate_directory(str(candidate_path), args.samples, args.module, scoring_fps=args.scoring_fps)
                    for _ in range(max(1, args.repeat))]
            scores = [run["score"] for run in runs]
            representative = min(runs, key=lambda run: abs(run["score"] - statistics.median(scores)))
            results.append({
                "index": index,
                "parameters": parameters,
                "score_median": statistics.median(scores),
                "score_min": min(scores),
                "metrics": representative,
            })
    results.sort(key=lambda item: (item["score_median"], item["score_min"]), reverse=True)
    output = {
        "base": args.base,
        "samples": args.samples,
        "module": args.module,
        "combination_count": len(results),
        "best": results[0],
        "results": results,
    }
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["best"], ensure_ascii=False, indent=2))
    if args.save_best:
        best_config = copy.deepcopy(base)
        for path, value in results[0]["parameters"].items():
            set_nested(best_config, path, value)
        destination = ROOT / "maixcam_app/configs/candidates" / (
            "sweep_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".yaml"
        )
        destination.write_text(json.dumps(best_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"saved best candidate to {destination}")


if __name__ == "__main__":
    main()
