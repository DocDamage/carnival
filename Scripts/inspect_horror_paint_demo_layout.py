"""Inspect the picture collection's sample display layout in the scratch project."""
import json
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival\Saved\WorldExpansion\AssetCompatProbe")
MAP = "/Game/HorrorPaintVol48/Maps/Demo"
OUT = ROOT / "Demo_Layout_Inspection.json"
report = {"map": MAP, "art": [], "walls": [], "errors": []}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError("Could not load " + MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for actor in actors:
        if not actor:
            continue
        label = actor.get_actor_label()
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.get_editor_property("static_mesh")
            if not mesh:
                continue
            name = mesh.get_name()
            box = mesh.get_bounding_box()
            row = {"actor": label, "component": comp.get_name(), "mesh": mesh.get_path_name(),
                   "location_cm": list(comp.get_world_location().to_tuple()),
                   "rotation_deg": list(comp.get_world_rotation().to_tuple()),
                   "scale": list(comp.get_world_scale().to_tuple()),
                   "mesh_dimensions_cm": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
                   "materials": [m.get_path_name() if m else None for m in comp.get_materials()]}
            if name.startswith("SM_Picture_") or name.startswith("SM_Photo_"):
                report["art"].append(row)
            elif any(token in name.lower() for token in ("wall", "frame")):
                report["walls"].append(row)
except Exception as exc:
    report["errors"].append(repr(exc))
finally:
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.SystemLibrary.quit_editor()
