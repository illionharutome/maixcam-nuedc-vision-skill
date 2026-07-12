"""Resume-safe OpenCV point annotator for laser/blob ground truth."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.tools.dataset_schema import image_paths, load_truth, save_truth


def main() -> None:
    parser = argparse.ArgumentParser(description="Click target centers and mark absent frames")
    parser.add_argument("--session", required=True, help="logs/tuning/session_name or a session directory")
    parser.add_argument("--start", type=int, default=0)
    args = parser.parse_args()
    session = Path(args.session)
    samples = session / "samples"
    metadata_path = session / "session.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    paths = image_paths(samples)
    if not paths:
        raise FileNotFoundError(f"no images in {samples}")
    truth = load_truth(samples)
    index = min(max(0, args.start), len(paths) - 1)
    clicked: list[tuple[int, int] | None] = [None]
    window = "MaixCAM ground truth"

    def mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            clicked[0] = (x, y)

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, mouse)
    while 0 <= index < len(paths):
        path = paths[index]
        frame = cv2.imread(str(path))
        if frame is None:
            index += 1
            continue
        existing = truth.get(path.name, {})
        point = clicked[0]
        if point is None and existing.get("present"):
            point = (int(existing["x"]), int(existing["y"]))
        view = frame.copy()
        if point is not None:
            cv2.drawMarker(view, point, (0, 255, 0), cv2.MARKER_CROSS, 18, 2)
        status = "UNLABELED" if not existing else ("PRESENT" if existing.get("present") else "ABSENT")
        cv2.putText(view, f"{index + 1}/{len(paths)} {path.name} [{status}]", (8, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(view, "click + ENTER=present | N=absent | B=back | S=skip | Q=save/quit", (8, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow(window, view)
        key = cv2.waitKey(0) & 0xFF
        common = {
            "scene": metadata.get("scene", "unassigned"),
            "lighting": metadata.get("lighting", "unknown"),
            "distance_mm": int(metadata.get("distance_mm", 0) or 0),
            "sequence": metadata.get("scene", session.name),
        }
        if key in (13, 10, 32):
            if point is None:
                continue
            truth[path.name] = {"present": True, "x": int(point[0]), "y": int(point[1]), **common}
            save_truth(samples, truth)
            clicked[0] = None
            index += 1
        elif key in (ord("n"), ord("N")):
            truth[path.name] = {"present": False, **common}
            save_truth(samples, truth)
            clicked[0] = None
            index += 1
        elif key in (ord("b"), ord("B")):
            clicked[0] = None
            index = max(0, index - 1)
        elif key in (ord("s"), ord("S")):
            clicked[0] = None
            index += 1
        elif key in (ord("q"), ord("Q"), 27):
            break
    save_truth(samples, truth)
    cv2.destroyAllWindows()
    print(f"saved {len(truth)}/{len(paths)} labels to {samples / 'ground_truth.json'}")


if __name__ == "__main__":
    main()
