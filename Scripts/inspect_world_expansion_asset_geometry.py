"""Record selected pack geometry, Blueprint composition, and reference candidates."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Asset_Geometry.json"
QUERIES = [
    ("Docks", "/Game/Docks/VOL2_Powell", ("SM_Pier", "SM_Sand_Plane", "SM_Pier_Tall_Pole", "SM_Lamp", "SM_Plank_Deck")),
    ("Prison", "/Game/HAUNTED_PRISON/Meshes", ("SM_MainTower", "SM_Tower", "SM_Floor", "SM_Stair", "SM_Door", "SM_WallExt", "SM_Pillar")),
    ("ResearchLab", "/Game/SciFiWorld/Modules/Meshes", ("SM_MFloor", "SM_MWall", "SM_MDoor", "SM_MStair")),
    ("Sewers", "/Game/Sewer/Meshes", ("SM_Sewer_Floor_01a", "SM_Sewer_Wall_Arch_01a", "SM_Sewer_Wall_Brick_01a", "SM_Sewer_Wall_Concrete_01a", "SM_IronPipe_straight_01")),
    ("Shipwreck", "/Game/UnderwaterShip/Meshes/Ship", ("SM_HullBroken", "SM_HullFront", "SM_HullMid", "SM_HullStern", "SM_Floor_MainDeck", "SM_Floor_Cabin", "SM_Wall_Hull", "SM_Door")),
]
BLUEPRINTS = [
    "/Game/HAUNTED_PRISON/Blueprints/BP_MainTower",
    "/Game/HAUNTED_PRISON/Blueprints/BP_Tower",
    "/Game/SciFiWorld/Blueprints/BP_LabCapsule01",
    "/Game/SciFiWorld/Blueprints/BP_LabHoloProjector01",
    "/Game/SciFiWorld/Blueprints/BP_BaseDoor",
    "/Game/UnderwaterShip/Blueprints/Ship/BP_Ship_HullBow",
]
report = {"mesh_candidates": [], "blueprints": [], "errors": []}
registry = unreal.AssetRegistryHelpers.get_asset_registry()


def mesh_report(mesh, package_name, asset_name):
    box = mesh.get_bounding_box()
    lo, hi = box.min.to_tuple(), box.max.to_tuple()
    body = mesh.get_editor_property("body_setup")
    try:
        flag = str(body.get_editor_property("collision_trace_flag")) if body else "missing"
    except Exception:
        flag = "unknown"
    return {"asset": package_name + "." + asset_name,
            "dimensions_cm": [hi[i] - lo[i] for i in range(3)],
            "bounds_min_cm": list(lo), "bounds_max_cm": list(hi),
            "collision_trace_flag": flag,
            "materials": [slot.material_interface.get_path_name() if slot.material_interface else None
                          for slot in mesh.get_editor_property("static_materials")]}


for pack, root_path, terms in QUERIES:
    try:
        for data in registry.get_assets_by_path(root_path, recursive=True):
            try:
                cls = str(data.asset_class_path.asset_name)
            except Exception:
                cls = str(data.asset_class)
            name = str(data.asset_name)
            if cls != "StaticMesh" or not any(term.lower() in name.lower() for term in terms):
                continue
            package, asset = str(data.package_name), name
            mesh = unreal.load_asset(package + "." + asset)
            if mesh:
                row = mesh_report(mesh, package, asset)
                row["pack"] = pack
                report["mesh_candidates"].append(row)
    except Exception:
        report["errors"].append({"query": root_path, "traceback": traceback.format_exc()})

world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for path in BLUEPRINTS:
    row = {"asset": path}
    try:
        bp = unreal.load_asset(path)
        if not bp or not hasattr(bp, "generated_class"):
            row["error"] = "Blueprint asset could not be loaded"
        else:
            cls = bp.generated_class()
            actor = eas.spawn_actor_from_class(cls, unreal.Vector(0, 0, 0))
            if not actor:
                row["error"] = "Generated class did not spawn as an actor"
            else:
                row["class"] = cls.get_path_name()
                center, extent = actor.get_actor_bounds(False, True)
                row["actor_bounds_cm"] = {"center": list(center.to_tuple()), "extent": list(extent.to_tuple())}
                components = []
                for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                    mesh = component.get_editor_property("static_mesh")
                    if mesh:
                        components.append({"mesh": mesh.get_path_name(),
                                           "relative_location": list(component.get_relative_location().to_tuple()),
                                           "relative_scale": list(component.get_relative_scale3d().to_tuple())})
                row["static_mesh_components"] = components
                eas.destroy_actor(actor)
    except Exception:
        row["traceback"] = traceback.format_exc()
    report["blueprints"].append(row)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("WORLD_EXPANSION_ASSET_GEOMETRY_COMPLETE")
unreal.SystemLibrary.quit_editor()
