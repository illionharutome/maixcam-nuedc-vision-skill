#!/usr/bin/env python3
import argparse,json,math,random
from pathlib import Path
from statistics import mean
def run(a):
 random.seed(7);aimx=aimy=0.;px=py=0.;dx=dy=0.;q=[]
 for i in range(600):
  tx=70*math.sin(i*a.target_motion_speed/90)+20*math.sin(i/17);ty=45*math.sin(i*a.target_motion_speed/120+1)+10*math.sin(i/11)
  ex=tx-aimx+random.gauss(0,a.noise_px);ey=ty-aimy+random.gauss(0,a.noise_px)
  pan=0 if abs(ex)<=a.deadband_px else max(-a.command_limit,min(a.command_limit,a.kp_x*ex+a.kd_x*(ex-dx)))
  tilt=0 if abs(ey)<=a.deadband_px else max(-a.command_limit,min(a.command_limit,a.kp_y*ey+a.kd_y*(ey-dy)))
  q.append({"t":i/30,"target_cx":tx,"target_cy":ty,"aim_x":aimx,"aim_y":aimy,"error_x":ex,"error_y":ey,"error":math.hypot(ex,ey),"pan_command":pan,"tilt_command":tilt,"ok":True,"fps":30.0,"status":"AIMED" if abs(ex)<=a.deadband_px and abs(ey)<=a.deadband_px else "TRACKING"})
  old=q[max(0,len(q)-1-a.delay_frames)];aimx+=old["pan_command"]*.12;aimy+=old["tilt_command"]*.12;dx,dy=ex,ey
 return q
def metrics(q,a):
 e=[r["error"] for r in q];return {"tracking_error_avg":mean(e),"tracking_error_max":max(e),"lock_time":next((r["t"] for r in q if r["error"]<=3),None),"lost_count":sum(not r["ok"] for r in q),"jitter":mean(abs(e[i]-e[i-1]) for i in range(1,len(e))),"overshoot":max(0,max(e[30:])-e[-1]),"saturation_rate":mean(max(abs(r["pan_command"]),abs(r["tilt_command"]))>=a.command_limit for r in q)}
def plot(q,path):
 try:import matplotlib.pyplot as plt
 except ImportError:print("matplotlib missing; plot skipped");return
 f,x=plt.subplots(3,1,figsize=(9,10));x[0].plot([r["t"] for r in q],[r["error_x"] for r in q],label="ex");x[0].plot([r["t"] for r in q],[r["error_y"] for r in q],label="ey");x[0].legend();x[1].plot([r["t"] for r in q],[r["pan_command"] for r in q],label="pan");x[1].plot([r["t"] for r in q],[r["tilt_command"] for r in q],label="tilt");x[1].legend();x[2].plot([r["target_cx"] for r in q],[r["target_cy"] for r in q]);x[2].set_title("manual target trajectory");f.tight_layout();f.savefig(path);plt.close(f)
def main():
 p=argparse.ArgumentParser();
 for n,d in (("kp_x",.3),("kp_y",.3),("kd_x",.08),("kd_y",.08),("deadband_px",3.),("command_limit",30.),("target_motion_speed",1.),("noise_px",1.)):p.add_argument("--"+n,type=float,default=d)
 p.add_argument("--delay_frames",type=int,default=2);p.add_argument("--no-plot",action="store_true");a=p.parse_args();q=run(a);out=Path(__file__).resolve().parents[1]/"logs"/"manual_tracking_sim.jsonl";out.parent.mkdir(exist_ok=True);out.write_text("".join(json.dumps(r)+"\n" for r in q));print(json.dumps(metrics(q,a),indent=2));
 if not a.no_plot:plot(q,out.with_suffix(".png"))
if __name__=="__main__":main()
