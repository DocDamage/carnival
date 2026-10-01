"""Read-only: collision setup of the prison entry wall meshes, and a render-free probe of the opening."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
R={'success':False,'errors':[],'meshes':{}}
try:
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if a.get_actor_label() in ('SM_WallEntry','SM_WallEntryInt','SM_DoorEntry','SM_DoorEntry_Frame','SM_Door_Prison','SM_Wall_Door_Prison','SM_SmallWallEntry'):
   m=a.static_mesh_component.static_mesh;bs=m.get_editor_property('body_setup')
   agg=bs.get_editor_property('agg_geom') if bs else None
   R['meshes'][a.get_actor_label()]={'mesh':m.get_path_name(),'trace_flag':str(bs.get_editor_property('collision_trace_flag')) if bs else None,
    'boxes':len(agg.get_editor_property('box_elems')) if agg else None,'convex':len(agg.get_editor_property('convex_elems')) if agg else None,
    'spheres':len(agg.get_editor_property('sphere_elems')) if agg else None,'location':[round(v) for v in a.get_actor_location().to_tuple()],
    'rotation':[round(v,1) for v in a.get_actor_rotation().to_tuple()],'scale':list(a.get_actor_scale3d().to_tuple()),
    'mesh_extent':[round(v) for v in m.get_bounds().box_extent.to_tuple()]}
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(ROOT/'Saved/WorldExpansion/PrisonGateCollision_20261001.json').write_text(json.dumps(R,indent=1))
