"""Read-only inspect ship painting meshes/materials and their placed instances."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Ship_Painting_Inspection.json"
MAP = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck"
ASSETS = [
    "/Game/UnderwaterShip/Meshes/Props/CabinLarge/SM_Frame",
    "/Game/UnderwaterShip/Materials/Furniture_Mat/MI_FramePainting",
    "/Game/UnderwaterShip/Textures/Props/T_FramePainting_B",
    "/Game/UnderwaterShip/Textures/Props/T_FramePainting_ORM",
]
report = {"map": MAP, "assets": [], "instances": [], "errors": []}

try:
    for path in ASSETS:
        asset = unreal.load_asset(path)
        if not asset:
            report["assets"].append({"path": path, "available": False})
            continue
        row = {"path": asset.get_path_name(), "class": asset.get_class().get_name()}
        if isinstance(asset, unreal.StaticMesh):
            box = asset.get_bounding_box()
            row["dimensions_cm"] = [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z]
            row["materials"] = [slot.material_interface.get_path_name() if slot.material_interface else None
                                for slot in asset.get_editor_property("static_materials")]
        if isinstance(asset, unreal.MaterialInstanceConstant):
            row["parent"] = asset.get_editor_property("parent").get_path_name()
            row["texture_parameters"] = []
            try:
                for info in unreal.MaterialEditingLibrary.get_texture_parameter_values(asset):
                    row["texture_parameters"].append({"name": info.parameter_info.name,
                                                       "texture": info.parameter_value.get_path_name() if info.parameter_value else None})
            except Exception as exc:
                row["texture_parameter_error"] = repr(exc)
        report["assets"].append(row)

    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError("Unable to load " + MAP)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors():
        if not actor:
            continue
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.get_editor_property("static_mesh")
            if not mesh or "SM_Frame" not in mesh.get_name():
                continue
            loc = comp.get_world_location()
            rot = comp.get_world_rotation()
            box = mesh.get_bounding_box()
            report["instances"].append({
                "actor": actor.get_actor_label(), "class": actor.get_class().get_name(),
                "level": actor.get_level().get_path_name(), "component": comp.get_name(),
                "mesh": mesh.get_path_name(), "materials": [m.get_path_name() if m else None for m in comp.get_materials()],
                "location_cm": list(loc.to_tuple()), "rotation_deg": list(rot.to_tuple()),
                "mesh_dimensions_cm": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
            })
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("SHIP_PAINTING_INSPECTION_" + ("COMPLETE" if not report["errors"] else "WITH_ERRORS"))
    unreal.SystemLibrary.quit_editor()
