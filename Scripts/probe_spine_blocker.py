"""Read-only: what blocks the outer spine near the prison approach (capsule sweeps along the route direction)."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
R={'success':False,'errors':[],'sweeps':[],'overlaps':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 p=V(-34309,-29485,720)
 for yaw in range(0,360,30):
  d=V(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)),0)
  h=t(unreal.SystemLibrary.capsule_trace_single(world,p,p+d*300,40,90,TQ,False,[],N,True))
  R['sweeps'].append({'yaw':yaw,'hit':bool(h),'dist':round((h[5]-p).length()) if h else None,'actor':h[9].get_actor_label() if h and h[9] else None,
   'level':h[9].get_level().get_outermost().get_name().split('/')[-1] if h and h[9] else None,'component':h[10].get_name() if h and h[10] else None,'normal':[round(v,2) for v in h[7].to_tuple()] if h else None})
 acts=unreal.SystemLibrary.box_overlap_actors(world,p,V(500,500,300),[],None,[])
 for a in acts or []:
  o,e=a.get_actor_bounds(False)
  R['overlaps'].append({'label':a.get_actor_label(),'class':a.get_class().get_name(),'level':a.get_level().get_outermost().get_name().split('/')[-1],'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]})
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(ROOT/'Saved/WorldExpansion/SpineBlocker_20261001.json').write_text(json.dumps(R,indent=1))
