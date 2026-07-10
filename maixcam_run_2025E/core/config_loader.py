"""Load JSON-compatible YAML without requiring a third-party module on MaixCAM."""

import json
import os


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
    with open(path, "r") as handle:
        text = handle.read()
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
            return _simple_yaml(text)


def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(filename):
    return load_yaml(os.path.join(project_root(), "config", filename))
