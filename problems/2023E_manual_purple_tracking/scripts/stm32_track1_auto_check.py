#!/usr/bin/env python3
import argparse,re,time
CASES=[("left_up","$MV,TRACK1,1,140,110,160,120,-20,-10,0.90,30.0,TRACKING#",lambda d:d["EX"]==-20 and d["EY"]==-10 and d["VALID"]==1 and d["STATE"]=="TRACKING"),("right_down","$MV,TRACK1,1,190,140,160,120,30,20,0.90,30.0,TRACKING#",lambda d:d["EX"]==30 and d["EY"]==20 and d["VALID"]==1),("no_target","$MV,TRACK1,0,0,0,160,120,0,0,0.00,30.0,NO_TARGET#",lambda d:d["PAN"]==0 and d["TILT"]==0 and d["VALID"]==0 and d["STATE"] in ("LOST","NO_TARGET")),("aimed","$MV,TRACK1,1,162,119,160,120,2,-1,0.95,30.0,AIMED#",lambda d:abs(d["PAN"])<=1 and abs(d["TILT"])<=1 and d["VALID"]==1 and d["STATE"] in ("AIMED","LOCKED"))]
def parse_dbg(text):
 m=re.search(r"\$DBG,TRACK1,([^#]+)#",text)
 if not m:return None
 d={}
 for item in m.group(1).split(","):
  k,s,v=item.partition("=")
  if s:d[k]=int(v) if k in ("EX","EY","PAN","TILT","VALID") else v
 return d
def exchange(port,packet,timeout):
 port.reset_input_buffer();port.write((packet+"\r\n").encode("ascii"));end=time.monotonic()+timeout;data=b""
 while time.monotonic()<end:
  data+=port.read(port.in_waiting or 1)
  if b"$DBG,TRACK1" in data and b"#" in data:break
 return data.decode("ascii",errors="replace")
def main():
 p=argparse.ArgumentParser();p.add_argument("--port",required=True);p.add_argument("--baud",type=int,default=115200);p.add_argument("--timeout",type=float,default=3);p.add_argument("--sign-x",type=int,choices=(-1,1),default=1);p.add_argument("--sign-y",type=int,choices=(-1,1),default=1);a=p.parse_args()
 try:import serial
 except ImportError:raise SystemExit("pyserial missing; run: python -m pip install pyserial")
 from pathlib import Path
 log=[];passed=True
 try:port=serial.Serial(a.port,a.baud,timeout=.1)
 except Exception as exc:raise SystemExit("cannot open %s: %s"%(a.port,exc))
 with port:
  for name,packet,check in CASES:
   response=exchange(port,packet,a.timeout);d=parse_dbg(response);ok=d is not None and check(d)
   if ok and name in ("left_up","right_down"):ok=(d["PAN"]*a.sign_x*d["EX"]>0 and d["TILT"]*a.sign_y*d["EY"]>0)
   passed&=ok;line="%s: %s SEND=%s RECV=%s"%(name,"PASS" if ok else "FAIL",packet,response.strip() or "TIMEOUT");print(line);log.append(line)
 out=Path(__file__).resolve().parents[1]/"logs"/"track1_auto_check.txt";out.parent.mkdir(exist_ok=True);out.write_text("\n".join(log),encoding="utf-8");raise SystemExit(0 if passed else 1)
if __name__=="__main__":main()
