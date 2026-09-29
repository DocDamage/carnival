"""Inspect prison tower construction pieces before any wall-art placement."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAP = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison"
OUT = ROOT / "Saved/WorldExpansion/Prison_Art_Locations.json"
report = {"map": MAP, "actors": [], "reference_mansion_pictures": [], "errors": []}

try:
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        raise RuntimeError("Unable to load " + MAP)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in eas.get_all_level_actors():
        if not actor:
            continue
        name = actor.get_actor_label()
        if not any(k in name.lower() for k in ("tower", "chapel", "office", "cell", "admin")):
            continue
        row = {"label": name, "class": actor.get_class().get_name(),
               "level": actor.get_level().get_path_name(),
               "location_cm": list(actor.get_actor_location().to_tuple()),
               "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
               "components": []}
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.get_editor_property("static_mesh")
            if not mesh:
                continue
            n = mesh.get_name().lower()
            if not any(k in n for k in ("wall", "door", "floor", "ceiling", "stair", "frame", "window", "pillar")):
                continue
            box = mesh.get_bounding_box()
            row["components"].append({
                "component": comp.get_name(), "mesh": mesh.get_path_name(),
                "location_cm": list(comp.get_world_location().to_tuple()),
                "rotation_deg": list(comp.get_world_rotation().to_tuple()),
                "scale": list(comp.get_world_scale().to_tuple()),
                "mesh_bounds_min_cm": list(box.min.to_tuple()),
                "mesh_bounds_max_cm": list(box.max.to_tuple()),
                "mesh_size_cm": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
                "materials": [m.get_path_name() if m else None for m in comp.get_materials()],
            })
        if row["components"] or any(k in name.lower() for k in ("tower", "chapel", "office", "cell", "admin")):
            report["actors"].append(row)

    mansion = "/Game/Carnival/World/Levels/L_HauntedMansionConnected"
    if not unreal.EditorLoadingAndSavingUtils.load_map(mansion):
        raise RuntimeError("Unable to load reference map " + mansion)
    for actor in eas.get_all_level_actors():
        if actor and "picture" in actor.get_actor_label().lower():
            report["reference_mansion_pictures"].append({
                "label": actor.get_actor_label(),
                "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
                "location_cm": list(actor.get_actor_location().to_tuple()),
            })
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("PRISON_ART_LOCATIONS_" + ("COMPLETE" if not report["errors"] else "WITH_ERRORS"))
    unreal.SystemLibrary.quit_editor()
