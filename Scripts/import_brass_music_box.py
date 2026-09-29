"""Import the authored mansion story prop as a cooked Unreal static mesh."""

import json
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
FBX_PATH = ROOT / "Saved/MansionConnection/Source/FBX/SM_BrassMusicBox.fbx"
DESTINATION = "/Game/Carnival/Props/Mission"
REPORT_PATH = ROOT / "Saved/MansionConnection/Music_Box_Asset.json"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
task = unreal.AssetImportTask()
task.filename = str(FBX_PATH)
task.destination_path = DESTINATION
task.destination_name = "SM_BrassMusicBox"
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
static_data = options.static_mesh_import_data
static_data.set_editor_property("convert_scene", True)
static_data.set_editor_property("convert_scene_unit", True)
static_data.set_editor_property("combine_meshes", True)
static_data.set_editor_property("generate_lightmap_u_vs", True)
task.options = options
asset_tools.import_asset_tasks([task])

asset_path = DESTINATION + "/SM_BrassMusicBox"
mesh = unreal.load_asset(asset_path)
if not mesh:
    raise RuntimeError(f"Unreal did not import {asset_path}")
box = mesh.get_bounding_box()
dimensions = [box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z]
if min(dimensions) <= 0 or max(dimensions) > 100.0:
    raise RuntimeError(f"Unexpected imported prop dimensions: {dimensions}")

material_slots = []
for slot in mesh.get_editor_property("static_materials"):
    material = slot.material_interface
    material_slots.append(material.get_path_name() if material else None)

unreal.EditorAssetLibrary.save_asset(asset_path)
report = {
    "fbx": str(FBX_PATH),
    "asset": mesh.get_path_name(),
    "dimensions_cm": dimensions,
    "material_slots": material_slots,
}
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"BRASS_MUSIC_BOX_IMPORTED {json.dumps(report)}")
unreal.SystemLibrary.quit_editor()
