"""Read wall transforms and bounds in the authored Research Lab B room."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAP = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB"
OUT = ROOT / "Saved/WorldExpansion/LabB_Wall_Transforms.json"
report = {"map": MAP, "walls": [], "art": [], "errors": []}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError("Could not load " + MAP)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors():
        if not actor:
            continue
        label = actor.get_actor_label()
        level = actor.get_level().get_path_name()
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.get_editor_property("static_mesh")
            if not mesh:
                continue
            mesh_name = mesh.get_name()
            box = mesh.get_bounding_box()
            row = {"actor": label, "level": level, "component": comp.get_name(),
                   "mesh": mesh.get_path_name(),
                   "location_cm": list(comp.get_world_location().to_tuple()),
                   "rotation_deg": list(comp.get_world_rotation().to_tuple()),
                   "scale": list(comp.get_world_scale().to_tuple()),
                   "mesh_dimensions_cm": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
                   "materials": [m.get_path_name() if m else None for m in comp.get_materials()]}
            if mesh_name.startswith("SM_MWall") or "wall" in mesh_name.lower():
                report["walls"].append(row)
            if mesh_name.startswith("SM_Picture_") or mesh_name.startswith("SM_Photo_"):
                report["art"].append(row)
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("LABB_WALL_TRANSFORMS_" + ("COMPLETE" if not report["errors"] else "WITH_ERRORS"))
    unreal.SystemLibrary.quit_editor()
