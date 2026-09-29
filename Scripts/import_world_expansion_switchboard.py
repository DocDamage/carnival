"""Import the selected G-drive switchboard prop and its source texture links."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
SOURCE = ROOT / "Saved/WorldExpansion/ExternalSource/IndustrialSwitchboard/source_extracted/FalllEctricBox.fbx"
DEST = "/Game/Carnival/WorldExpansion/IndustrialSwitchboard"
REPORT = ROOT / "Saved/WorldExpansion/IndustrialSwitchboard_Import.json"
report = {"success": False, "source": str(SOURCE), "destination": DEST}
try:
    task = unreal.AssetImportTask()
    task.filename = str(SOURCE)
    task.destination_path = DEST
    task.destination_name = "SM_IndustrialSwitchboard"
    task.automated = True
    task.replace_existing = False
    task.save = True
    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_as_skeletal = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials = True
    options.import_textures = True
    options.import_animations = False
    options.static_mesh_import_data.set_editor_property("convert_scene", True)
    options.static_mesh_import_data.set_editor_property("convert_scene_unit", True)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(DEST + "/SM_IndustrialSwitchboard")
    if not mesh:
        raise RuntimeError("Unreal did not import the switchboard mesh")
    box = mesh.get_bounding_box()
    report.update({
        "success": True,
        "asset": mesh.get_path_name(),
        "dimensions_cm": [box.max.to_tuple()[i] - box.min.to_tuple()[i] for i in range(3)],
        "material_slots": [str(item.material_slot_name) for item in mesh.get_editor_property("static_materials")],
        "textures": [name for name in unreal.EditorAssetLibrary.list_assets(DEST, recursive=True, include_folder=False)],
    })
except Exception as exc:
    report.update({"error": repr(exc), "traceback": traceback.format_exc()})
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("WORLD_EXPANSION_SWITCHBOARD_" + ("IMPORTED" if report.get("success") else "FAILED"))
    unreal.SystemLibrary.quit_editor()
