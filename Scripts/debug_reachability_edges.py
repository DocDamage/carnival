import json,os,math
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
src=(ROOT/'Scripts/audit_region_reachability.py').read_text()
os.environ['CARNIVAL_REGION']='labs'
# Reuse definitions only: stop before the work begins.
head=src[:src.index("try:\n t0=time.time()")].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(head,'audit_defs','exec'),g)
V=unreal.Vector;world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
TQ,N,t=g['TQ'],g['N'],g['t']
out=[]
# walk a line across Lab A's step group: from floor (local x -150) to platform (local x -650), local y 225
A=(-42097.962876199206,-7043.716818882417);Y=math.radians(-57)
def W(lx,ly):return (A[0]+math.cos(Y)*lx-math.sin(Y)*ly,A[1]+math.sin(Y)*lx+math.cos(Y)*ly)
prev=None
for lx in range(-150,-700,-50):
 x,y=W(lx,225)
 h=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,900),V(x,y,450),TQ,False,[],N,True))
 z=h[5].z if h else None
 row={'lx':lx,'floor':round(z,1) if z else None,'actor':h[9].get_actor_label() if h and h[9] else None,'normal':round(h[7].z,2) if h else None}
 if h:
  c=V(x,y,z+98);b=t(unreal.SystemLibrary.capsule_trace_single(world,c,c+V(0,0,.1),42,96,TQ,False,[],N,True))
  row['standing']=(b[9].get_actor_label() if b[9] else '?') if b else 'clear'
  if prev:
   hi,lo=max(z,prev[2]),min(z,prev[2])
   m=t(unreal.SystemLibrary.line_trace_single(world,V((x+prev[0])/2,(y+prev[1])/2,hi+60),V((x+prev[0])/2,(y+prev[1])/2,lo-80),TQ,False,[],N,True))
   row['mid']=round(m[5].z,1) if m else None
   zz=hi+110;bb=t(unreal.SystemLibrary.capsule_trace_single(world,V(prev[0],prev[1],zz),V(x,y,zz),42,60,TQ,False,[],N,True))
   row['body']=(bb[9].get_actor_label() if bb[9] else '?') if bb else 'clear'
  prev=(x,y,z)
 out.append(row)
(ROOT/'Saved/WorldExpansion/Reachability/debug_lab_steps.json').write_text(json.dumps(out,indent=1))
