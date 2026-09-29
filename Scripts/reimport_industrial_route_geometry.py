"""Back up and reimport explicitly selected generated route meshes only."""
import json
import shutil
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital"
BASE = "/Game/Carnival/World/Meshes/IndustrialHospital"
names = globals().get("MESH_NAMES", ["SM_IndustrialSlums_TerrainPatch"])
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report = {"success": False, "meshes": []}
for name in names:
    if not (name == "SM_IndustrialSlums_TerrainPatch" or name.startswith("SM_IndustrialHospital_Road_")):
        raise ValueError("Not a generated route mesh: " + name)
    path = BASE + "/" + name
    original = unreal.load_asset(path)
    if not original:
        raise RuntimeError("Expected mesh is missing: " + path)
    materials = list(original.get_editor_property("static_materials"))
    asset_file = ROOT / "Content/Carnival/World/Meshes/IndustrialHospital" / (name + ".uasset")
    backup = OUT / "Backups" / (name + "_before_geometry_correction_" + stamp + ".uasset")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(asset_file, backup)
    task = unreal.AssetImportTask()
    task.filename = str(OUT / "Source/FBX" / (name + ".fbx"))
    task.destination_path = BASE
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False
    options = unreal.FbxImportUI()
    options.import_materials = False
    options.import_textures = False
    options.import_as_skeletal = False
    options.automated_import_should_detect_type = False
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not task.get_editor_property("imported_object_paths"):
        raise RuntimeError("Import produced no assets: " + name)
    mesh = unreal.load_asset(path)
    mesh.set_editor_property("static_materials", materials)
    mesh.get_editor_property("body_setup").set_editor_property(
        "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, False):
        raise RuntimeError("Could not save " + path)
    report["meshes"].append({"path": path, "backup": str(backup)})
report["success"] = True
(OUT / "Geometry_Reimport.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
