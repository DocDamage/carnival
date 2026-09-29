"""Import the authored foyer-glove, paper note, and study-key static meshes into Unreal."""

import json
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
SOURCE = ROOT / "Saved/MissionAuthoring/Source/FBX"
DESTINATION = "/Game/Carnival/Props/Mission"
REPORT = ROOT / "Saved/MissionAuthoring/Mission_Clue_Props_Import.json"
NAMES = ("SM_WetWorkGlove", "SM_EliFoyerNote", "SM_BrassServiceKey")

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
results = []
for name in NAMES:
    fbx = SOURCE / f"{name}.fbx"
    if not fbx.is_file():
        raise RuntimeError(f"Missing authored FBX: {fbx}")
    task = unreal.AssetImportTask()
    task.filename = str(fbx)
    task.destination_path = DESTINATION
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True

    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_as_skeletal = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials = True
    options.import_textures = False
    options.import_animations = False
    options.static_mesh_import_data.set_editor_property("convert_scene", True)
    options.static_mesh_import_data.set_editor_property("convert_scene_unit", True)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
    task.options = options
    asset_tools.import_asset_tasks([task])

    asset = unreal.load_asset(f"{DESTINATION}/{name}")
    if not asset:
        raise RuntimeError(f"Unreal did not import {name}")
    bounds = asset.get_bounding_box()
    dimensions = [bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z]
    if min(dimensions) <= 0 or max(dimensions) > 40.0:
        raise RuntimeError(f"Unexpected dimensions for {name}: {dimensions}")
    unreal.EditorAssetLibrary.save_asset(f"{DESTINATION}/{name}")
    materials = [
        slot.material_interface.get_path_name() if slot.material_interface else None
        for slot in asset.get_editor_property("static_materials")
    ]
    results.append({
        "asset": asset.get_path_name(),
        "source_fbx": str(fbx),
        "dimensions_cm": dimensions,
        "materials": materials,
    })

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"success": True, "props": results}, indent=2), encoding="utf-8")
unreal.log("MISSION_CLUE_PROPS_IMPORTED " + json.dumps(results))
unreal.SystemLibrary.quit_editor()
