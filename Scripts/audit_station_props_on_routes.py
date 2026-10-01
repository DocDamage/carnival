"""Read-only: which campaign station props stand on road/route surfaces."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
ROUTE_WORDS=('Road','Route','Segment','Quay','Pier','Walk','Approach','Driveway','Forecourt','Crossing','Trail','Path','Bridge','Spline')
R={'success':False,'errors':[],'props':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 props=[a for a in acts if a.get_actor_label().startswith('Campaign_') and a.get_actor_label().endswith('_Prop')]
 for a in props:
  o,e=a.get_actor_bounds(False);hits=[]
  for fx,fy in ((0,0),(1,1),(1,-1),(-1,1),(-1,-1)):
   p=V(o.x+fx*(e.x+30),o.y+fy*(e.y+30),o.z)
   h=t(unreal.SystemLibrary.line_trace_single(world,V(p.x,p.y,o.z+e.z+50),V(p.x,p.y,o.z-e.z-400),TQ,False,props,N,True))
   if h:hits.append(h[9].get_actor_label() if h[9] else '')
  on_route=sorted({x for x in hits if any(w.lower() in x.lower() for w in ROUTE_WORDS)})
  R['props'].append({'label':a.get_actor_label(),'level':a.get_level().get_outermost().get_name().split('/')[-1],'origin':[round(v) for v in o.to_tuple()],'floor':sorted(set(hits)),'on_route_surface':on_route})
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(ROOT/'Saved/CampaignAcceptance/StationPropsOnRoutesAfterResite_20261001.json').write_text(json.dumps(R,indent=1))
