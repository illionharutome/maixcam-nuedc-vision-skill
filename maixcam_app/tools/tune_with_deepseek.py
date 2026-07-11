"""Ask DeepSeek for a candidate config, replay it, and promote only if better."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.tools.replay_test import evaluate_directory

ALLOWED_INPUTS = ("frames.jsonl", "metrics.json", "current_config.yaml", "failure_cases.json")


def read_inputs(session: Path) -> dict:
    data = {}
    for name in ALLOWED_INPUTS:
        path = session / name
        if not path.exists():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8")
        data[name] = text[-60000:] if name == "frames.jsonl" else text
    return data


def request_candidate(inputs: dict) -> dict:
    api_key = os.environ["DEEPSEEK_API_KEY"]
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    prompt = (
        "Return JSON only. Propose one conservative detector configuration based exclusively on the supplied "
        "structured logs. Schema: {\"candidate\": <complete config object>, \"rationale\": [strings]}. "
        "Do not include secrets, code, paths, or instructions. Prefer small threshold changes.\n" + json.dumps(inputs, ensure_ascii=False)
    )
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": "You tune classical vision thresholds and output strict JSON."},
                     {"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "max_tokens": 4096,
        "stream": False,
    }).encode("utf-8")
    request = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body,
                                     headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.load(response)
    content = payload["choices"][0]["message"]["content"]
    if not content:
        raise RuntimeError("DeepSeek returned empty JSON content")
    result = json.loads(content)
    if not isinstance(result.get("candidate"), dict):
        raise ValueError("response must contain a candidate object")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--module", default="laser_spot")
    args = parser.parse_args()
    session = Path(args.session)
    response = request_candidate(read_inputs(session))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate_dir = ROOT / "maixcam_app/configs/candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = candidate_dir / f"candidate_{stamp}.yaml"
    candidate_path.write_text(json.dumps(response["candidate"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics = evaluate_directory(str(candidate_path), str(session / "samples"), args.module)
    metrics_path = candidate_path.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    best_dir = ROOT / "maixcam_app/configs/best"
    best_metrics_path = best_dir / "current_best.metrics.json"
    old_score = float("-inf")
    if best_metrics_path.exists():
        old_score = json.loads(best_metrics_path.read_text(encoding="utf-8"))["score"]
    if metrics["sample_count"] > 0 and metrics["score"] > old_score:
        best_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate_path, best_dir / "current_best.yaml")
        shutil.copy2(metrics_path, best_metrics_path)
        print(f"promoted candidate score={metrics['score']:.4f}")
    else:
        print(f"candidate retained without promotion score={metrics['score']:.4f} best={old_score:.4f}")


if __name__ == "__main__":
    main()

