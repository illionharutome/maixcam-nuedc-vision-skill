"""Compare module/config pairs over one replay sample directory."""

from __future__ import annotations

import argparse
import json

from replay_test import evaluate_directory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", required=True)
    parser.add_argument("--case", action="append", required=True, help="module=config_path")
    args = parser.parse_args()
    results = []
    for case in args.case:
        module, config = case.split("=", 1)
        results.append({"module": module, "config": config, **evaluate_directory(config, args.samples, module)})
    results.sort(key=lambda item: item["score"], reverse=True)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

