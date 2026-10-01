import json,math,os
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
os.environ['CARNIVAL_REGION']='hospital_fine'
src=(ROOT/'Scripts/audit_region_reachability.py').read_text()
head=src[:src.index("try:\n t0=time.time()")].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(head,'defs','exec'),g)
V=unreal.Vector;TQ,N,t=g['TQ'],g['N'],g['t']
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
out=[]
lx,ly=100600,126850
pts=[(lx+k*50,ly) for k in range(0,9)]
prev=None
for x,y in pts:
 col=[];top=1400
 for _ in range(6):
  h=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,top),V(x,y,450),TQ,False,[],N,True))
  if not h:break
  z=h[5].z;ok=None
  if h[7].z>=.707:
   c=V(x,y,z+112);b=t(unreal.SystemLibrary.capsule_trace_single(world,c,c+V(0,0,.1),42,80,TQ,False,[],N,True))
   ok=(b[9].get_actor_label() if b and b[9] else 'clear')
  col.append([round(z),round(h[7].z,2),h[9].get_actor_label() if h[9] else '',ok]);top=z-40
 out.append({'x':x,'layers':col})
 # edge test between consecutive upper layers near 1000-1100
 cur=[l for l in col if 980<=l[0]<=1110 and l[3]=='clear']
 if prev and cur:
  a,b=prev,cur[0];pa=V(prev_xy[0],prev_xy[1],a[0]);pb=V(x,y,b[0]);hi,lo=max(a[0],b[0]),min(a[0],b[0])
  m=t(unreal.SystemLibrary.line_trace_single(world,V((pa.x+pb.x)/2,(pa.y+pb.y)/2,hi+60),V((pa.x+pb.x)/2,(pa.y+pb.y)/2,lo-80),TQ,False,[],N,True))
  bb=t(unreal.SystemLibrary.capsule_trace_single(world,V(pa.x,pa.y,hi+100),V(pb.x,pb.y,hi+100),42,50,TQ,False,[],N,True))
  out[-1]['edge_from_prev']={'dz':b[0]-a[0],'mid':round(m[5].z) if m else None,'mid_actor':m[9].get_actor_label() if m and m[9] else None,'body':(bb[9].get_actor_label() if bb and bb[9] else 'clear')}
 prev=cur[0] if cur else None;prev_xy=(x,y)
(ROOT/'Saved/WorldExpansion/Reachability/debug_audit_edge.json').write_text(json.dumps(out,indent=1))
