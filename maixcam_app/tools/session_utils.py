"""Safe session allocation for repeated MaixCAM experiments."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

SESSION_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def prepare_session(root: Path, requested_name: str, *, overwrite: bool = False) -> Path:
    """Return an empty session path without ever deleting outside *root*."""
    if not SESSION_NAME.fullmatch(requested_name) or requested_name in {".", ".."}:
        raise ValueError("session name must use only letters, digits, dot, underscore, or hyphen")
    root.mkdir(parents=True, exist_ok=True)
    resolved_root = root.resolve()
    target = root / requested_name
    if overwrite:
        resolved_target = target.resolve()
        if resolved_target.parent != resolved_root:
            raise ValueError("session path escaped logs/tuning")
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        return target
    if not target.exists() or not any(target.iterdir()):
        target.mkdir(parents=True, exist_ok=True)
        return target
    for index in range(2, 1000):
        candidate = root / f"{requested_name}_{index:03d}"
        if not candidate.exists() or not any(candidate.iterdir()):
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
    raise RuntimeError("could not allocate a unique session suffix")

