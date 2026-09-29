"""Import a focused Atlantis FBX subset and record UE-native geometry facts."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
SOURCE = ROOT / "Saved/WorldExpansion/Atlantis_FBX"
DESTINATION = "/Game/Atlantis_Ruins/Meshes"
REPORT = ROOT / "Saved/WorldExpansion/Atlantis_Import.json"
COLLIDING_PREFIXES = ("SM_Arch", "SM_Column", "SM_Rock", "SM_Rocks", "SM_Statue")

report = {"success": False, "destination": DESTINATION, "meshes": [], "errors": []}
try:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    for source in sorted(SOURCE.glob("*.fbx")):
        name = source.stem
        path = DESTINATION + "/" + name
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            task = unreal.AssetImportTask()
            task.filename = str(source)
            task.destination_path = DESTINATION
            task.destination_name = name
            task.automated = True
            task.replace_existing = False
            task.save = True
            options = unreal.FbxImportUI()
            options.automated_import_should_detect_type = False
            options.import_as_skeletal = False
            options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
            options.import_materials = False
            options.import_textures = False
            options.import_animations = False
            data = options.static_mesh_import_data
            for key, value in {
                "convert_scene": True,
                "convert_scene_unit": True,
                "combine_meshes": True,
                "generate_lightmap_u_vs": True,
                "auto_generate_collision": name.startswith(COLLIDING_PREFIXES),
            }.items():
                data.set_editor_property(key, value)
            task.options = options
            asset_tools.import_asset_tasks([task])
        mesh = unreal.load_asset(path)
        if not mesh:
            raise RuntimeError("Failed to import static mesh " + path)
        bounds = mesh.get_bounding_box()
        dimensions = [bounds.max.to_tuple()[i] - bounds.min.to_tuple()[i] for i in range(3)]
        slots = list(mesh.get_editor_property("static_materials"))
        body = mesh.get_editor_property("body_setup")
        collisions = bool(body and body.get_editor_property("agg_geom"))
        report["meshes"].append({
            "asset": mesh.get_path_name(),
            "source_fbx": str(source),
            "bounds_min_cm": list(bounds.min.to_tuple()),
            "bounds_max_cm": list(bounds.max.to_tuple()),
            "dimensions_cm": dimensions,
            "material_slots": [str(slot.material_slot_name) for slot in slots],
            "collision_geometry_present": collisions,
        })
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    report["success"] = True
except Exception as exc:
    report["errors"].append(repr(exc))
    report["traceback"] = traceback.format_exc()
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("ATLANTIS_FBX_IMPORT_" + ("COMPLETE" if report["success"] else "FAILED"))
    unreal.SystemLibrary.quit_editor()
