"""Repository structure, safety, test-surface, and Git state checks."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> tuple[int, str]:
    process = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    return process.returncode, process.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    checks: list[tuple[str, bool, str]] = []

    def exists(label: str, relative: str) -> None:
        path = ROOT / relative
        checks.append((label, path.exists(), relative))

    exists("Skill", "skills/maixcam_tmx_vision_competition/SKILL.md")
    exists("VisionResult interface", "maixcam_app/modules/base.py")
    exists("MaixCAM modules", "maixcam_app/modules")
    exists("TMX controller", "controller_tmx_mspm0")
    exists("LP-MSPM0G3507 integration", "controller_lp_mspm0g3507/README.md")
    exists("LP-MSPM0G3507 SysConfig", "controller_lp_mspm0g3507/empty.syscfg")
    exists("DCC migration notes", "controller_tmx_mspm0/dcc_reference_notes.md")
    exists("UART protocol", "controller_tmx_mspm0/protocol.md")
    exists("DeepSeek tuning", "maixcam_app/tools/tune_with_deepseek.py")
    exists("Ground-truth annotation", "maixcam_app/tools/annotate_samples.py")
    exists("Camera parameter sweep", "maixcam_app/tools/camera_sweep.py")
    exists("Dataset validation", "maixcam_app/tools/dataset_report.py")
    exists("Parameter sweep", "maixcam_app/tools/parameter_sweep.py")
    exists("YOLO training", "yolo_training/README.md")
    exists("Git ignore", ".gitignore")
    base_text = (ROOT / "maixcam_app/modules/base.py").read_text(encoding="utf-8")
    checks.append(("Unified result fields", all(name in base_text for name in ("target_x", "center_x", "confidence", "status", "extra")), "base.py"))

    _, tracked_text = git("ls-files")
    tracked = [line for line in tracked_text.splitlines() if line]
    forbidden_suffixes = {".pt", ".onnx", ".mud", ".mp4", ".avi", ".zip"}
    bad_paths = [path for path in tracked if Path(path).suffix.lower() in forbidden_suffixes or Path(path).name == ".env" or path.startswith("logs/")]
    checks.append(("No forbidden tracked artifacts", not bad_paths, ", ".join(bad_paths) or "clean"))
    large = [path for path in tracked if (ROOT / path).is_file() and (ROOT / path).stat().st_size > 10 * 1024 * 1024]
    checks.append(("No tracked file above 10 MiB", not large, ", ".join(large) or "clean"))
    secret_pattern = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
    secrets = []
    for relative in tracked:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            if secret_pattern.search(path.read_text(encoding="utf-8")):
                secrets.append(relative)
        except UnicodeDecodeError:
            continue
    checks.append(("No API-key-shaped text", not secrets, ", ".join(secrets) or "clean"))

    _, status = git("status", "--porcelain")
    checks.append(("Working tree clean", args.allow_dirty or not status, "allowed during pre-commit" if args.allow_dirty and status else status or "clean"))
    _, remotes = git("remote")
    if "origin" in remotes.splitlines():
        code, upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        if code == 0:
            _, counts = git("rev-list", "--left-right", "--count", f"{upstream}...HEAD")
            behind, ahead = (int(value) for value in counts.split())
            checks.append(("Remote synchronized", ahead == 0, f"behind={behind}, ahead={ahead}"))
        else:
            checks.append(("Remote synchronized", False, "origin exists but branch has no upstream"))
    else:
        todo = ROOT / "docs/git_remote_todo.md"
        recorded = todo.exists() and "没有配置 remote" in todo.read_text(encoding="utf-8")
        checks.append(("Push state recorded", recorded, "no origin; reason documented" if recorded else "no origin and no reason"))

    for label, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {label}: {detail}")
    failures = sum(not passed for _, passed, _ in checks)
    print(f"\n{len(checks) - failures}/{len(checks)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
