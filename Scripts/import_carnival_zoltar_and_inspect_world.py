"""Copy/import the user's Zoltar prop and locate the existing Carnival play area."""
import json
import shutil
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
SOURCE_ROOT = Path(r"G:\3d assets\Zoltar_Machine-331b8a9b\fbx")
STAGING = ROOT / "Saved/WorldExpansion/ExternalSource/AdditionalAssets/Zoltar_Machine"
SOURCE_FBX = STAGING / "zoltar.fbx"
THUMBNAIL = STAGING / "thumbnail.jpg"
DEST = "/Game/Carnival/WorldExpansion/CarnivalProps"
ASSET_NAME = "SM_ZoltarFortuneTeller"
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT = ROOT / "Saved/WorldExpansion/Zoltar_Import_And_Carnival_Inspection.json"

report = {"success": False, "source": str(SOURCE_ROOT / "zoltar.fbx"), "destination": DEST,
          "map": MAP, "candidate_actors": [], "errors": []}
try:
    STAGING.mkdir(parents=True, exist_ok=True)
    if not SOURCE_FBX.exists():
        shutil.copy2(SOURCE_ROOT / "zoltar.fbx", SOURCE_FBX)
    if not THUMBNAIL.exists():
        shutil.copy2(SOURCE_ROOT / "thumbnail.jpg", THUMBNAIL)

    task = unreal.AssetImportTask()
    task.filename = str(SOURCE_FBX)
    task.destination_path = DEST
    task.destination_name = ASSET_NAME
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
    mesh = unreal.load_asset(DEST + "/" + ASSET_NAME)
    if not mesh:
        raise RuntimeError("Unreal did not import the Zoltar static mesh")
    bounds = mesh.get_bounding_box()
    report["asset"] = mesh.get_path_name()
    report["dimensions_cm"] = [bounds.max.x - bounds.min.x,
                               bounds.max.y - bounds.min.y,
                               bounds.max.z - bounds.min.z]
    report["materials"] = [slot.material_interface.get_path_name() if slot.material_interface else None
                           for slot in mesh.get_editor_property("static_materials")]
    report["source_sha256"] = __import__("hashlib").sha256(SOURCE_FBX.read_bytes()).hexdigest()

    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError("Could not load the active Carnival map")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    terms = ("carniv", "circus", "tent", "wheel", "carousel", "clown", "ride", "stall",
             "ticket", "booth", "balloon", "fortune", "bigtop", "ferris")
    for actor in eas.get_all_level_actors():
        if not actor:
            continue
        label = actor.get_actor_label()
        components = []
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            sm = comp.get_editor_property("static_mesh")
            if sm:
                components.append(sm.get_path_name())
        haystack = (label + " " + actor.get_class().get_name() + " " + " ".join(components)).lower()
        if not any(term in haystack for term in terms):
            continue
        location = actor.get_actor_location()
        center, extent = actor.get_actor_bounds(False, True)
        report["candidate_actors"].append({
            "label": label,
            "class": actor.get_class().get_name(),
            "outer": actor.get_outer().get_path_name(),
            "location_cm": list(location.to_tuple()),
            "bounds_center_cm": list(center.to_tuple()),
            "bounds_extent_cm": list(extent.to_tuple()),
            "meshes": components[:12],
        })
    report["success"] = True
except Exception as exc:
    report["errors"].append(repr(exc))
    report["traceback"] = traceback.format_exc()
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("ZOLTAR_IMPORT_AND_CARNIVAL_INSPECTION_" + ("SUCCESS" if report["success"] else "FAILED"))
    unreal.SystemLibrary.quit_editor()
