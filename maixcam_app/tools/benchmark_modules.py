"""Compare module/config pairs over one replay sample directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.tools.replay_test import evaluate_directory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", required=True)
    parser.add_argument("--case", action="append", required=True, help="module=config_path")
    parser.add_argument("--scoring-fps", type=float, default=0.0)
    args = parser.parse_args()
    results = []
    for case in args.case:
        module, config = case.split("=", 1)
        results.append({"module": module, "config": config,
                        **evaluate_directory(config, args.samples, module, scoring_fps=args.scoring_fps)})
    results.sort(key=lambda item: item["score"], reverse=True)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
