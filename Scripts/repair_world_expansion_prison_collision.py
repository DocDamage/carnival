import json
from pathlib import Path
import unreal
ROOT=Path(r"F:\Carnival"); package="/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison"
out=ROOT/"Saved/WorldExpansion/Prison_Collision_Repair.json"
world=unreal.EditorLoadingAndSavingUtils.load_map(package)
if not world: raise RuntimeError("Could not open authored Prison level")
rows=[]
for actor in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    if actor.get_name() not in ("StaticMeshActor_1","StaticMeshActor_15"): continue
    component=actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh=component.get_editor_property("static_mesh") if component else None
    if not component or not mesh or mesh.get_path_name()!="/Engine/BasicShapes/Plane.Plane": continue
    before=unreal.SystemLibrary.line_trace_single.__name__ if False else "blocking profile retained"
    component.set_collision_profile_name("NoCollision")
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    rows.append({"actor":actor.get_path_name(),"label":actor.get_actor_label(),"mesh":mesh.get_path_name(),"collision_profile":"NoCollision","visual_retained":True})
if len(rows)!=2: raise RuntimeError("Expected exactly the two known giant showcase planes; changed %d"%len(rows))
if not unreal.EditorLoadingAndSavingUtils.save_map(world,package): raise RuntimeError("Could not save repaired Prison level")
out.write_text(json.dumps({"success":True,"actors":rows},indent=2),encoding="utf-8")
unreal.SystemLibrary.quit_editor()
