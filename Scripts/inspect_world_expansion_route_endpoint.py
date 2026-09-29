import json,math
from pathlib import Path
import unreal
ROOT=Path(r"F:\\Carnival")
MAP="/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
TARGET=unreal.Vector(-69966.343,-85850.278,500.0)
OUT=ROOT/"Saved/WorldExpansion/Route_Endpoint_Inspection.json"
world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world: raise RuntimeError("Could not load Carnival map")
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows=[]
for actor in eas.get_all_level_actors():
    try:
        center,extent=actor.get_actor_bounds(False,True)
        dx=max(0.0,abs(center.x-TARGET.x)-extent.x); dy=max(0.0,abs(center.y-TARGET.y)-extent.y); dz=max(0.0,abs(center.z-TARGET.z)-extent.z)
        distance=math.sqrt(dx*dx+dy*dy+dz*dz)
        if distance>900 and actor.get_name()!="StaticMeshActor_14": continue
        row={"name":actor.get_name(),"label":actor.get_actor_label(),"class":actor.get_class().get_name(),"location":actor.get_actor_location().to_tuple(),"bounds_center":center.to_tuple(),"bounds_extent":extent.to_tuple(),"distance_aabb_cm":distance}
        comp=actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            mesh=comp.get_editor_property("static_mesh")
            row["mesh"]=mesh.get_path_name() if mesh else None
            row["collision_profile"]=str(comp.get_editor_property("collision_profile_name"))
            row["collision_enabled"]=str(comp.get_editor_property("collision_enabled"))
        rows.append(row)
    except Exception: pass
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"target":TARGET.to_tuple(),"actors":sorted(rows,key=lambda x:x["distance_aabb_cm"])},indent=2),encoding="utf-8")
unreal.SystemLibrary.quit_editor()
