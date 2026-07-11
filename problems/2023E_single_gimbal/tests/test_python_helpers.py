import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "maixvision_project"
sys.path.insert(0, str(PROJECT))

from comm.protocol_single import serialize_single
from core.result import VisionResult


def main():
    result = VisionResult(True, 140, 110, 160, 120, -20, -10,
                          "CENTER", 0, 0.9, 30.0, "TRACKING")
    assert serialize_single(result) == "$MV,SINGLE,1,140,110,160,120,-20,-10,CENTER,0,0.9,30,TRACKING#"
    result.score = result.fps = 0.0
    assert ",0,0,TRACKING#" in serialize_single(result)

    module_path = ROOT / "scripts" / "stm32_2023e_single_auto_check.py"
    spec = importlib.util.spec_from_file_location("single_auto_check", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parsed = module.parse_dbg(
        "$DBG,SINGLE,EX=-12,EY=8,PAN=-300,TILT=200,VALID=1,PATH=CENTER,STEP=0,STATUS=TRACKING,STATE=TRACKING#"
    )
    assert parsed["PAN"] == -300 and parsed["VALID"] == 1
    print("Python helper tests passed")


if __name__ == "__main__":
    main()
