"""Load JSON-compatible YAML without requiring a third-party module on MaixCAM."""

import json
import os


DEFAULT_CONFIGS = {
    "camera.yaml": {"width": 320, "height": 240, "fps": 30, "buffer_num": 3},
    "uart.yaml": {"enabled": False, "device": "auto", "baudrate": 115200},
    "target_board.yaml": {"mode": "fixed_center"},
    "aiming.yaml": {
        "aimed_threshold_x": 8,
        "aimed_threshold_y": 8,
        "aimed_required_frames": 3,
        "lost_timeout_ms": 300,
    },
}


def _scalar(value):
    value = value.strip()
    if value in ("true", "True"):
        return True
    if value in ("false", "False"):
        return False
    if value in ("null", "None", "~"):
        return None
    if value.startswith("[") and value.endswith("]"):
        return [_scalar(item) for item in value[1:-1].split(",") if item.strip()]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _simple_yaml(text):
    """Parse the deliberately small map/list subset used by config/*.yaml."""
    root = {}
    stack = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, sep, value = line.strip().partition(":")
        if not sep:
            raise ValueError("invalid YAML line: %s" % raw_line)
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        value = value.strip()
        if value:
            parent[key] = _scalar(value)
        else:
            child = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def load_yaml(path):
    try:
        with open(path, "r") as handle:
            text = handle.read()
    except OSError as exc:
        raise ValueError("cannot read config '%s': %s" % (path, exc))
    # JSON is a YAML subset. Permit leading YAML comments while keeping the
    # runtime dependency-free on MaixCAM when PyYAML is unavailable.
    json_text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    try:
        return json.loads(json_text)
    except ValueError:
        try:
            import yaml  # Optional when deployed with PyYAML.
            return yaml.safe_load(text)
        except ImportError:
            try:
                return _simple_yaml(text)
            except ValueError as exc:
                raise ValueError("cannot parse YAML config '%s': %s" % (path, exc))


def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(filename):
    path = os.path.join(project_root(), "config", filename)
    if not os.path.exists(path):
        defaults = DEFAULT_CONFIGS.get(filename)
        if defaults is not None:
            print("WARNING: config '%s' is missing; using safe defaults" % filename)
            return dict(defaults)
        raise ValueError("config '%s' was not found at %s" % (filename, path))
    config = load_yaml(path)
    if not isinstance(config, dict):
        raise ValueError("config '%s' must contain a YAML mapping" % filename)
    defaults = DEFAULT_CONFIGS.get(filename, {})
    merged = dict(defaults)
    merged.update(config)
    return merged
