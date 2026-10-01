"""Read-only: blockers at the mansion-walk stall and the hospital-road motorcycle stall."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
R={'success':False,'errors':[],'points':{}}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def info(a):
 if not a:return None
 o,e=a.get_actor_bounds(False)
 m=a.static_mesh_component.static_mesh.get_path_name() if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh else None
 return {'label':a.get_actor_label(),'name':a.get_name(),'class':a.get_class().get_name(),'level':a.get_level().get_outermost().get_name().split('/')[-1],'mesh':m,'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]}
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 for name,p in (('mansion_walk_stall',V(-68627,-82904,698)),('hospital_moto_stall',V(90609,118604,690))):
  sw=[]
  for yaw in range(0,360,45):
   d=V(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)),0)
   h=t(unreal.SystemLibrary.capsule_trace_single(world,p,p+d*250,40,90,TQ,False,[],N,True))
   sw.append({'yaw':yaw,'dist':round((h[5]-p).length()) if h else None,'actor':info(h[9]) if h else None})
  acts=unreal.SystemLibrary.box_overlap_actors(world,p,V(250,250,200),[],None,[]) or []
  R['points'][name]={'sweeps':sw,'overlaps':[info(a) for a in acts]}
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if a.get_name()=='StaticMeshActor_1163':R['StaticMeshActor_1163']=info(a)
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(ROOT/'Saved/WorldExpansion/RouteBlockersR02R07_20261001.json').write_text(json.dumps(R,indent=1))
