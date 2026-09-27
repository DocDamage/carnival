"""Import route meshes, the supplied factory facade, and local sound sources."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Import_Route_Assets.json"
REPORT = {"imports": [], "errors": []}
tools = unreal.AssetToolsHelpers.get_asset_tools()


def run_import(filename, destination_path, destination_name, kind):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(filename))
    task.set_editor_property("destination_path", destination_path)
    task.set_editor_property("destination_name", destination_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", False)
    if kind == "fbx":
        options = unreal.FbxImportUI()
        options.set_editor_property("import_materials", False)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("import_as_skeletal", False)
        options.set_editor_property("automated_import_should_detect_type", False)
        task.set_editor_property("options", options)
    tools.import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths"))
    REPORT["imports"].append({
        "source": str(filename),
        "destination": destination_path + "/" + destination_name,
        "kind": kind,
        "imported_paths": paths,
        "asset_exists": bool(unreal.EditorAssetLibrary.does_asset_exist(destination_path + "/" + destination_name)),
    })


try:
    fbx_root = ROOT / "Saved/IndustrialHospital/Source/FBX"
    mesh_dir = "/Game/Carnival/World/Meshes/IndustrialHospital"
    facade_dir = "/Game/IndustrialSlums/IndustrialHospital_Facade"
    audio_dir = "/Game/Carnival/Audio/IndustrialHospital"
    for folder in (mesh_dir, facade_dir, audio_dir):
        unreal.EditorAssetLibrary.make_directory(folder)

    for source in sorted(fbx_root.glob("SM_IndustrialHospital_Road_*.fbx")):
        name = source.stem
        if not unreal.EditorAssetLibrary.does_asset_exist(mesh_dir + "/" + name):
            run_import(source, mesh_dir, name, "fbx")
        else:
            REPORT["imports"].append({"destination": mesh_dir + "/" + name, "kind": "fbx", "already_present": True})

    terrain_fbx = fbx_root / "SM_IndustrialSlums_TerrainPatch.fbx"
    terrain_name = "SM_IndustrialSlums_TerrainPatch"
    if not unreal.EditorAssetLibrary.does_asset_exist(mesh_dir + "/" + terrain_name):
        run_import(terrain_fbx, mesh_dir, terrain_name, "fbx")
    else:
        REPORT["imports"].append({"destination": mesh_dir + "/" + terrain_name, "kind": "fbx", "already_present": True})

    facade_fbx = ROOT / "Saved/IndustrialHospital/Source/Facade_1M_6x8K/FBX_1_mln_6x8K/FBX_1_mln_6x8K.fbx"
    facade_name = "SM_IndustrialHospital_FactoryFacade"
    if not unreal.EditorAssetLibrary.does_asset_exist(facade_dir + "/" + facade_name):
        run_import(facade_fbx, facade_dir, facade_name, "fbx")
    else:
        REPORT["imports"].append({"destination": facade_dir + "/" + facade_name, "kind": "fbx", "already_present": True})

    audio_root = ROOT / "Saved/IndustrialHospital/Source/Audio"
    for source in sorted(audio_root.glob("*.mp3")):
        name = source.stem.replace(" ", "_")
        if not unreal.EditorAssetLibrary.does_asset_exist(audio_dir + "/" + name):
            run_import(source, audio_dir, name, "audio")
        else:
            REPORT["imports"].append({"destination": audio_dir + "/" + name, "kind": "audio", "already_present": True})

    for item in REPORT["imports"]:
        path = item.get("destination")
        if path and unreal.EditorAssetLibrary.does_asset_exist(path):
            obj = unreal.load_asset(path)
            item["class"] = obj.get_class().get_name() if obj else None
            if obj and obj.get_class().get_name() == "SoundWave":
                obj.set_editor_property("looping", True)
                unreal.EditorAssetLibrary.save_loaded_asset(obj, False)
    REPORT["phase"] = "complete"
except Exception as exc:
    REPORT["phase"] = "failed"
    REPORT["error"] = repr(exc)
    REPORT["traceback"] = traceback.format_exc()

OUT.write_text(json.dumps(REPORT, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_HOSPITAL_ROUTE_ASSETS_" + REPORT["phase"].upper())
unreal.SystemLibrary.quit_editor()
