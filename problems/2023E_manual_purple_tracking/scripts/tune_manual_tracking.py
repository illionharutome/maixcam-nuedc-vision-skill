#!/usr/bin/env python3
import argparse,json,math,os
from pathlib import Path
from statistics import mean,pstdev
def analyze(rows):
 valid=[r for r in rows if r.get("ok")];e=[float(r.get("error",math.hypot(r.get("error_x",0),r.get("error_y",0)))) for r in valid];fps=[float(r["fps"]) for r in rows if "fps" in r];cmd=[max(abs(r.get("pan_command",0)),abs(r.get("tilt_command",0))) for r in rows];limit=max(cmd,default=0);tail=e[-60:]
 return {"error_avg":mean(e) if e else None,"error_max":max(e) if e else None,"error_std":pstdev(e) if len(e)>1 else 0,"lock_time":next((r.get("t") for r in valid if r.get("error",999)<=3),None),"jitter":mean(abs(tail[i]-tail[i-1]) for i in range(1,len(tail))) if len(tail)>1 else 0,"overshoot":max(0,max(e[30:],default=0)-e[-1]) if e else None,"saturation_rate":mean(c>=limit and limit>0 for c in cmd) if cmd else 0,"lost_count":len(rows)-len(valid),"fps_avg":mean(fps) if fps else None,"fps_min":min(fps) if fps else None}
def advice(s):
 a=[]
 if s["lock_time"] is None or s["lock_time"]>2:a.append("检查 kp_x/kp_y 与目标移动速度")
 if s["overshoot"] and s["overshoot"]>5:a.append("考虑增加 kd_x/kd_y 或降低 kp")
 if s["jitter"]>1:a.append("考虑 deadband_px 或 smoothing_alpha")
 a.append("实板前分别检查 sign_x/sign_y；禁止凭仿真假设方向")
 return a
def call_api(summary):
 key=os.environ.get("DEEPSEEK_API_KEY")
 if not key:raise SystemExit("--deepseek requires DEEPSEEK_API_KEY")
 import urllib.request
 body=json.dumps({"model":"deepseek-chat","messages":[{"role":"system","content":"Only suggest parameters. Never apply configuration or control hardware."},{"role":"user","content":"Aggregate summary: "+json.dumps(summary)}]}).encode();req=urllib.request.Request("https://api.deepseek.com/v1/chat/completions",data=body,headers={"Content-Type":"application/json","Authorization":"Bearer "+key})
 with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read())["choices"][0]["message"]["content"]
def main():
 p=argparse.ArgumentParser();p.add_argument("--file",type=Path);p.add_argument("--deepseek",action="store_true");a=p.parse_args();path=a.file or Path(__file__).resolve().parents[1]/"logs"/"manual_tracking_sim.jsonl";rows=[json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()];s=analyze(rows);print(json.dumps(s,indent=2));print("suggestions:");[print("-",x) for x in advice(s)];
 if a.deepseek:print(call_api(s))
 print("No configuration changed; no command sent.")
if __name__=="__main__":main()
