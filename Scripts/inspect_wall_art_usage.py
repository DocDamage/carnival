"""Audit existing picture/painting placement and available wall-art assets."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Wall_Art_Usage_Inspection.json"
MAPS = [
    ("carnival_root", "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"),
    ("connected_mansion", "/Game/Carnival/World/Levels/L_HauntedMansionConnected"),
    ("mansion_source", "/Game/Mansion/Levels/LV_Haunted_Mansion"),
    ("research_lab_b", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB"),
    ("prison", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison"),
    ("shipwreck", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck"),
]
ASSETS = [
    "/Game/Mansion/Mesh/Assets/Pictures/SM_Picture01",
    "/Game/Mansion/Mesh/Assets/Pictures/SM_Picture02",
    "/Game/Mansion/Mesh/Assets/Pictures/SM_Picture03",
    "/Game/Mansion/Mesh/Assets/Pictures/SM_Picture04",
    "/Game/Gladiator_Arena/Mesh/SM_Paintings_a",
    "/Game/Gladiator_Arena/Mesh/SM_Paintings_b",
    "/Game/Gladiator_Arena/Mesh/SM_Paintings_c",
    "/Game/Town/Meshes/Props/SM_Painting_01",
    "/Game/Town/Meshes/Props/SM_Painting_02",
    "/Game/Town/Meshes/Props/SM_Painting_03",
]
report = {"maps": [], "assets": [], "errors": []}
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
    for asset_path in ASSETS:
        mesh = unreal.load_asset(asset_path)
        if not mesh:
            report["assets"].append({"path": asset_path, "available": False})
            continue
        box = mesh.get_bounding_box()
        materials = [slot.material_interface.get_path_name() if slot.material_interface else None
                     for slot in mesh.get_editor_property("static_materials")]
        report["assets"].append({"path": mesh.get_path_name(), "available": True,
                                 "dimensions_cm": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
                                 "materials": materials})
    for label, path in MAPS:
        try:
            world = unreal.EditorLoadingAndSavingUtils.load_map(path)
            if not world:
                raise RuntimeError("Could not load map " + path)
            pictures, walls = [], []
            for actor in eas.get_all_level_actors():
                if not actor:
                    continue
                outer = actor.get_outer().get_path_name()
                actor_label = actor.get_actor_label()
                components = actor.get_components_by_class(unreal.StaticMeshComponent)
                for component in components:
                    mesh = component.get_editor_property("static_mesh")
                    if not mesh:
                        continue
                    mesh_path = mesh.get_path_name()
                    if any(word in (actor_label + " " + mesh_path).lower()
                           for word in ("picture", "painting", "portrait", "framepainting")):
                        center, extent = actor.get_actor_bounds(False, True)
                        pictures.append({"actor": actor_label, "class": actor.get_class().get_name(),
                                         "outer": outer, "mesh": mesh_path,
                                         "location_cm": list(actor.get_actor_location().to_tuple()),
                                         "bounds_center_cm": list(center.to_tuple()),
                                         "bounds_extent_cm": list(extent.to_tuple())})
                    if ("wall" in (actor_label + " " + mesh_path).lower() or "partition" in mesh_path.lower()):
                        center, extent = actor.get_actor_bounds(False, True)
                        if max(extent.x, extent.y) >= 180 and extent.z >= 120:
                            walls.append({"actor": actor_label, "class": actor.get_class().get_name(),
                                          "outer": outer, "mesh": mesh_path,
                                          "location_cm": list(actor.get_actor_location().to_tuple()),
                                          "bounds_center_cm": list(center.to_tuple()),
                                          "bounds_extent_cm": list(extent.to_tuple())})
            report["maps"].append({"label": label, "map": path, "picture_placements": pictures,
                                   "wall_candidates": walls[:180],
                                   "picture_count": len(pictures), "wall_candidate_count": len(walls)})
        except Exception:
            report["errors"].append({"map": path, "traceback": traceback.format_exc()})
except Exception:
    report["errors"].append({"traceback": traceback.format_exc()})
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("WALL_ART_USAGE_INSPECTION_" + ("COMPLETE" if not report["errors"] else "WITH_ERRORS"))
    unreal.SystemLibrary.quit_editor()
