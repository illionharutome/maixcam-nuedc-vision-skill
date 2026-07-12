"""Validate label completeness and scene balance before replay scoring."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.tools.dataset_schema import validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    report = validate_dataset(Path(args.samples))
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    raise SystemExit(0 if report["ready_for_scoring"] else 2)


if __name__ == "__main__":
    main()
