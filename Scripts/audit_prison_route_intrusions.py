"""Read-only: prison-level colliding actors intersecting connector route segments, plus the prison's large Plane actors."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
V=unreal.Vector
R={'success':False,'errors':[],'planes':[],'intrusions':{}}
try:
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 lv=lambda a:a.get_level().get_outermost().get_name().split('/')[-1]
 prison=[a for a in acts if lv(a)=='L_CarnivalWorldExpansion_Prison']
 segs=[a for a in acts if lv(a)=='L_CarnivalWorldExpansion_Connections_Layout' and isinstance(a,unreal.StaticMeshActor)]
 for a in prison:
  if a.get_actor_label().startswith('Plane'):
   c=a.static_mesh_component;o,e=a.get_actor_bounds(False)
   R['planes'].append({'label':a.get_actor_label(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else None,'collision':str(c.get_collision_enabled()),
    'profile':str(c.get_collision_profile_name()),'visible':not a.is_hidden_ed() and c.is_visible(),'hidden_in_game':a.is_hidden_ed(),
    'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()],'scale':[round(v,2) for v in a.get_actor_scale3d().to_tuple()],'rotation':[round(v,2) for v in a.get_actor_rotation().to_tuple()]})
 for a in prison:
  if a.get_actor_label().startswith('Plane'):continue
  comps=a.get_components_by_class(unreal.PrimitiveComponent)
  if not any(str(c.get_collision_enabled())!='CollisionEnabled.NO_COLLISION' for c in comps):continue
  o,e=a.get_actor_bounds(False)
  for s in segs:
   so,se=s.get_actor_bounds(False)
   if all(abs(o.to_tuple()[i]-so.to_tuple()[i])<=e.to_tuple()[i]+se.to_tuple()[i]+ (0 if i<2 else 200) for i in range(3)):
    R['intrusions'].setdefault(a.get_actor_label(),{'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()],'segments':[]})['segments'].append(s.get_actor_label())
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(ROOT/'Saved/WorldExpansion/PrisonRouteIntrusions_20261001.json').write_text(json.dumps(R,indent=1))
