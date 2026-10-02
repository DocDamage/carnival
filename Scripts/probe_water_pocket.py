"""Read-only: what is at a single water pocket the shore audit found without an exit (env CARNIVAL_POCKET=x,y).
Column profile (all hits from high to low), a 1 m grid of floor tops and actors within 8 m, and waist-height rays
at the water surface."""
import json,math,os,traceback
from pathlib import Path
import unreal
X,Y=[float(v) for v in os.environ.get('CARNIVAL_POCKET','-14750,-14250').split(',')]
OUT=Path(r'F:\Carnival\Saved\WorldExpansion')/('WaterPocket_%d_%d_20261001.json'%(X,Y))
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE;SURF=-240
R={'success':False,'errors':[],'pocket':[X,Y]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def nm(h):return h[9].get_actor_label() if h and h[9] else ''
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ign=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 col=[];z=3000.0;skip=list(ign)
 for _ in range(8):
  h=t(unreal.SystemLibrary.line_trace_single(w,V(X,Y,z),V(X,Y,-6000),TQ,False,skip,N,True))
  if not h:break
  col.append([nm(h),round(h[5].z),round(h[7].z,2)]);skip.append(h[9]);z=h[5].z-1
 R['column']=col
 grid=[]
 for j in range(8,-9,-2):
  row=[]
  for i in range(-8,9,2):
   h=t(unreal.SystemLibrary.line_trace_single(w,V(X+i*100,Y+j*100,3000),V(X+i*100,Y+j*100,-6000),TQ,False,ign,N,True))
   row.append(round(h[5].z) if h else None)
  grid.append(row)
 R['floor_grid_2m']=grid
 R['rays']=[]
 for yaw in range(0,360,30):
  d=V(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)),0);s=V(X,Y,SURF+50)
  h=t(unreal.SystemLibrary.line_trace_single(w,s,s+d*1500,TQ,False,ign,N,True))
  R['rays'].append([yaw,round(h[3]) if h else None,nm(h)])
 R['nearby']=sorted([[round(math.dist((X,Y),(a.get_actor_location().x,a.get_actor_location().y))),a.get_actor_label(),a.get_level().get_outermost().get_name().split('/')[-1]]
  for a in acts if math.dist((X,Y),(a.get_actor_location().x,a.get_actor_location().y))<1500])[:25]
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
