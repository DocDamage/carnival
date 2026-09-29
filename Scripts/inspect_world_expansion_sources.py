"""Inspect supplied demo maps, selected assets, bounds, and package dependencies."""
import json
import traceback
from collections import Counter
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Source_Inspection.json"
MAPS = [
    ("docks_day_reference", "/Game/Docks/VOL2_Powell/Maps/LIGHTING_DAY"),
    ("docks_night_reference", "/Game/Docks/VOL2_Powell/Maps/LIGHTING_NIGHT"),
    ("prison_overview_reference", "/Game/HAUNTED_PRISON/Levels/L_Overview"),
    ("lab_room_a_reference", "/Game/SciFiWorld/Maps/SciFiCreaturesResearchRoomA"),
    ("lab_room_b_reference", "/Game/SciFiWorld/Maps/SciFiCreaturesResearchRoomB"),
    ("sewer_full_reference", "/Game/Sewer/Levels/L_Sewer"),
    ("sewer_corridor_reference", "/Game/Sewer/Levels/L_Sewers_Corridor"),
    ("sewer_pier_reference", "/Game/Sewer/Levels/L_Sewers_Pier"),
    ("shipwreck_exterior_reference", "/Game/UnderwaterShip/Levels/UnderwaterShip_Showcase_Exterior"),
]
ASSETS = [
    "/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Short_Narrow",
    "/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Short_Destroyed_A",
    "/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Tall_Destroyed_A",
    "/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_A",
    "/Game/HAUNTED_PRISON",
    "/Game/SciFiWorld",
    "/Game/Sewer/Meshes/Kit_Concrete/Arch/SM_Sewer_Wall_Arch_01a",
    "/Game/Sewer/Meshes/Kit_Brick/SM_Sewer_Wall_Brick_01a",
    "/Game/Sewer/Meshes/SM_Sewer_Floor_01a",
    "/Game/UnderwaterShip/Meshes",
]
report = {"maps": [], "assets": [], "errors": []}
OUT.parent.mkdir(parents=True, exist_ok=True)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
registry = unreal.AssetRegistryHelpers.get_asset_registry()


def save():
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")


def mesh_info(mesh):
    bounds = mesh.get_bounding_box()
    lo, hi = bounds.min.to_tuple(), bounds.max.to_tuple()
    body = mesh.get_editor_property("body_setup")
    try:
        collision = body.get_editor_property("collision_trace_flag") if body else None
        collision = str(collision)
    except Exception:
        collision = "unknown"
    return {"asset": mesh.get_path_name(),
            "bounds_min_cm": list(lo), "bounds_max_cm": list(hi),
            "dimensions_cm": [hi[i] - lo[i] for i in range(3)],
            "material_slots": [
                slot.material_interface.get_path_name() if slot.material_interface else None
                for slot in mesh.get_editor_property("static_materials")
            ], "collision_trace_flag": collision}


def inspect_asset_path(path):
    package_path = path.rsplit("/", 1)[0] if path.count("/") > 3 else path
    rows = []
    for data in registry.get_assets_by_path(package_path, recursive=True):
        try:
            cls = str(data.asset_class_path.asset_name)
        except Exception:
            cls = str(data.asset_class)
        if cls in ("StaticMesh", "Blueprint", "World", "MaterialInstanceConstant"):
            rows.append({"asset": str(data.package_name) + "." + str(data.asset_name), "class": cls})
    report["assets"].append({"query": path, "found": unreal.EditorAssetLibrary.does_asset_exist(path),
                             "assets": rows[:80], "asset_count": len(rows)})


for path in ASSETS:
    try:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            asset = unreal.load_asset(path)
            if isinstance(asset, unreal.StaticMesh):
                row = mesh_info(asset)
                row["query"] = path
                report["assets"].append(row)
            else:
                inspect_asset_path(path)
        else:
            inspect_asset_path(path)
    except Exception:
        report["errors"].append({"asset": path, "traceback": traceback.format_exc()})
    save()

for label, path in MAPS:
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(path)
        if not world:
            raise RuntimeError("load_map returned null")
        actors = list(eas.get_all_level_actors())
        class_counts = Counter(actor.get_class().get_name() for actor in actors)
        bounds = []
        mesh_paths = Counter()
        actor_rows = []
        for actor in actors:
            try:
                center, extent = actor.get_actor_bounds(False, True)
                e = extent.to_tuple()
                if max(e) > 0.0 and max(e) < 50000.0:
                    bounds.append((center.to_tuple(), e))
            except Exception:
                pass
            try:
                for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                    mesh = component.get_editor_property("static_mesh")
                    if mesh:
                        mesh_paths[mesh.get_path_name()] += 1
            except Exception:
                pass
            if len(actor_rows) < 160:
                actor_rows.append({"label": actor.get_actor_label(),
                                   "class": actor.get_class().get_name(),
                                   "location_cm": list(actor.get_actor_location().to_tuple())})
        area_bounds = None
        if bounds:
            area_bounds = {
                "min_cm": [min(c[i] - e[i] for c, e in bounds) for i in range(3)],
                "max_cm": [max(c[i] + e[i] for c, e in bounds) for i in range(3)],
            }
            area_bounds["dimensions_cm"] = [area_bounds["max_cm"][i] - area_bounds["min_cm"][i] for i in range(3)]
        row = {"label": label, "map": path, "loaded_world": world.get_path_name(),
               "actor_count": len(actors), "class_counts": dict(class_counts),
               "world_bounds": area_bounds,
               "placed_meshes": [{"asset": name, "instances": count}
                                 for name, count in mesh_paths.most_common(80)],
               "actors_sample": actor_rows}
        report["maps"].append(row)
        save()
        unreal.log("WORLD_EXPANSION_SOURCE_INSPECTED " + label + " actors=" + str(len(actors)))
    except Exception:
        report["errors"].append({"map": path, "traceback": traceback.format_exc()})
        save()

save()
unreal.log("WORLD_EXPANSION_SOURCE_INSPECTION_COMPLETE")
unreal.SystemLibrary.quit_editor()
