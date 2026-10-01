"""Read-only: slab top vs underlying ground along the first/last 80 m of the outer spine."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
REG=json.loads((ROOT/'Saved/WorldExpansion/Region_Authoring.json').read_text())
C=REG.get('outer_route_spine',{}).get('controls_cm') or [c for c in REG['connections'] if c['id']=='R03'][0]['route']['spine_controls_cm']
R={'success':False,'errors':[],'ends':{}}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 segs=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='OuterRoute_Segment']
 R['segment_count']=len(segs)
 for name,(a,b) in (('mansion',(C[0],C[1])),('hospital',(C[-1],C[-2]))):
  d=[b[0]-a[0],b[1]-a[1]];L=math.hypot(*d);u=(d[0]/L,d[1]/L);n=(-u[1],u[0])
  rows=[]
  for s in range(-1500,8001,250):
   for lat in (-300,0,300):
    x,y=a[0]+u[0]*s+n[0]*lat,a[1]+u[1]*s+n[1]*lat
    top=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,a[2]+800),V(x,y,a[2]-800),TQ,False,[],N,True))
    under=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,a[2]+800),V(x,y,a[2]-800),TQ,False,segs,N,True))
    rows.append({'s':s,'lat':lat,'top_z':round(top[5].z) if top else None,'top':top[9].get_actor_label() if top and top[9] else None,
     'under_z':round(under[5].z) if under else None,'under':under[9].get_actor_label() if under and under[9] else None})
  R['ends'][name]={'start':a,'dir':u,'rows':rows}
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(ROOT/'Saved/WorldExpansion/SpineEndProfiles_20261001.json').write_text(json.dumps(R,indent=1))
