"""Inspect candidate wall surfaces in the shipwreck interior without saving it."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAP = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck"
OUT = ROOT / "Saved/WorldExpansion/Shipwreck_Wall_Candidates.json"
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
            row = {
                "actor": label,
                "level": level,
                "component": comp.get_name(),
                "mesh": mesh.get_path_name(),
                "location_cm": list(comp.get_world_location().to_tuple()),
                "rotation_deg": list(comp.get_world_rotation().to_tuple()),
                "materials": [m.get_path_name() if m else None for m in comp.get_materials()],
            }
            box = mesh.get_bounding_box()
            row["mesh_dimensions_cm"] = [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z]
            center, extent = actor.get_actor_bounds(False, True)
            row["actor_bounds_center_cm"] = list(center.to_tuple())
            row["actor_bounds_extent_cm"] = list(extent.to_tuple())
            if any(token in (label + " " + mesh.get_name()).lower() for token in ("wall", "bulkhead", "frame", "picture")):
                if "frame" in mesh.get_name().lower() or "picture" in mesh.get_name().lower():
                    report["art"].append(row)
                else:
                    report["walls"].append(row)
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("SHIPWRECK_WALL_INSPECTION_" + ("COMPLETE" if not report["errors"] else "WITH_ERRORS"))
    unreal.SystemLibrary.quit_editor()
