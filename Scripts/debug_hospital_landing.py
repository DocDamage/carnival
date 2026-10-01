import json,math,os,collections
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
os.environ['CARNIVAL_REGION']='hospital_fine'
src=(ROOT/'Scripts/audit_region_reachability.py').read_text()
head=src[:src.index("try:\n t0=time.time()")].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(head,'defs','exec'),g)
V=unreal.Vector;TQ,N,t=g['TQ'],g['N'],g['t']
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
res=[]
# Sweep outward from both stairwell landings at z~1063/1093 in 8 directions, recording floor heights and blockers.
for name,(lx,ly) in (('stairwell_1',(95300,125100)),('stairwell_2',(100600,126850))):
 for ang in range(0,360,45):
  d=(math.cos(math.radians(ang)),math.sin(math.radians(ang)));row={'well':name,'ang':ang,'steps':[]}
  for k in range(0,12):
   x,y=lx+d[0]*k*50,ly+d[1]*k*50
   h=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,1250),V(x,y,980),TQ,False,[],N,True))
   if not h:row['steps'].append([k,None]);continue
   c=V(x,y,h[5].z+112);b=t(unreal.SystemLibrary.capsule_trace_single(world,c,c+V(0,0,.1),42,80,TQ,False,[],N,True))
   row['steps'].append([k,round(h[5].z),h[9].get_actor_label() if h[9] else '',(b[9].get_actor_label() if b and b[9] else None)])
  res.append(row)
(ROOT/'Saved/WorldExpansion/Reachability/debug_hospital_landing.json').write_text(json.dumps(res,indent=1))
