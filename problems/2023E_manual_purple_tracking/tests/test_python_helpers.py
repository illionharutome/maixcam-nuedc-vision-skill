import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"maixvision_project"))
from core.result import TrackResult
from comm.protocol_track1 import serialize_track1
from vision.aim_calibration import AimCalibration
r=TrackResult(True,140,110,160,120,-20,-10,100,.9,30,"TRACKING")
assert serialize_track1(r)=="$MV,TRACK1,1,140,110,160,120,-20,-10,0.9,30,TRACKING#"
spec=importlib.util.spec_from_file_location("check",ROOT/"scripts"/"stm32_track1_auto_check.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=m.parse_dbg("$DBG,TRACK1,EX=-20,EY=-10,PAN=-300,TILT=-200,VALID=1,STATUS=TRACKING,STATE=TRACKING#");assert d["PAN"]==-300 and d["STATE"]=="TRACKING"
aim=AimCalibration({"aim_cx":160,"aim_cy":120,"threshold_x":8,"threshold_y":8,"aimed_required_frames":3})
r.target_cx,r.target_cy=162,119
assert aim.evaluate(r)[2]=="TRACKING";assert aim.evaluate(r)[2]=="TRACKING";assert aim.evaluate(r)[2]=="AIMED"
print("TRACK1 Python tests passed")
