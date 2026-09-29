import json
from pathlib import Path
import unreal
ROOT=Path(r"F:\Carnival"); out=ROOT/"Saved/WorldExpansion/Prison_Collision_Inspection.json"
world=unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
targets=["L_CarnivalWorldExpansion_Prison.L_CarnivalWorldExpansion_Prison:PersistentLevel.StaticMeshActor_15","L_CarnivalWorldExpansion_Prison.L_CarnivalWorldExpansion_Prison:PersistentLevel.StaticMeshActor_1"]
rows=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 path=a.get_path_name()
 if not any(x in path for x in targets): continue
 c,e=a.get_actor_bounds(False,True)
 row={"path":path,"location":a.get_actor_location().to_tuple(),"bounds_center":c.to_tuple(),"bounds_extent":e.to_tuple(),"class":a.get_class().get_name()}
 for comp in a.get_components_by_class(unreal.PrimitiveComponent):
  cr={"name":comp.get_name(),"class":comp.get_class().get_name()}
  for prop in ("collision_enabled","collision_profile_name","object_type","relative_location","relative_rotation","relative_scale3d"):
   try:
    v=comp.get_editor_property(prop); cr[prop]=v.to_tuple() if hasattr(v,"to_tuple") else str(v)
   except Exception as ex: cr[prop+"_error"]=repr(ex)
  if isinstance(comp,unreal.StaticMeshComponent):
   m=comp.get_editor_property("static_mesh"); cr["mesh"]=m.get_path_name() if m else None
  row.setdefault("components",[]).append(cr)
 rows.append(row)
out.write_text(json.dumps(rows,indent=2),encoding="utf-8")
unreal.SystemLibrary.quit_editor()
