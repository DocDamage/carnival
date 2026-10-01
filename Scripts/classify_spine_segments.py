"""Read-only: for each OuterRoute_Segment, the walkable surface beneath it (ignoring all spine segments)."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
R={'success':False,'errors':[],'segments':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 segs=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='OuterRoute_Segment']
 for a in segs:
  o,e=a.get_actor_bounds(False);top=o.z+e.z
  f=a.get_actor_forward_vector();rgt=a.get_actor_right_vector();sx=a.get_actor_scale3d()
  hx,hy=50*abs(sx.x),50*abs(sx.y)
  samples=[]
  for fx,fy in ((0,0),(.9,.9),(.9,-.9),(-.9,.9),(-.9,-.9),(.9,0),(-.9,0),(0,.9),(0,-.9)):
   p=V(o.x+f.x*hx*fx+rgt.x*hy*fy,o.y+f.y*hx*fx+rgt.y*hy*fy,0)
   h=t(unreal.SystemLibrary.line_trace_single(world,V(p.x,p.y,top+300),V(p.x,p.y,top-1500),TQ,False,segs,N,True))
   samples.append({'z':round(h[5].z,1),'walk':h[7].z>=.7,'actor':h[9].get_actor_label() if h[9] else ''} if h else None)
  R['segments'].append({'name':a.get_name(),'origin':[round(v) for v in o.to_tuple()],'top':round(top,1),'half':[round(hx),round(hy)],'yaw':round(a.get_actor_rotation().yaw,1),
   'pitch':round(a.get_actor_rotation().pitch,2),'roll':round(a.get_actor_rotation().roll,2),'under':samples})
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(ROOT/'Saved/WorldExpansion/SpineSegmentClassification_20261001.json').write_text(json.dumps(R,indent=1))
