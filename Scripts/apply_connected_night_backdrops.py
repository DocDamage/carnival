"""Calibrate copied coastal backdrop materials for the connected night world.

The RailBridge source instances were authored for daylight exposure (emissive
1000 and 2254). Keep the source pack intact and override only the five backdrop
components in the connected coastal level, using local material instances.
"""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital"
LEVEL = "/Game/Carnival/World/Levels/L_CoastalMansionApproach"
DEST = "/Game/Carnival/World/Materials/ConnectedNight"
EMISSIVE = 0.08
report = {"success": False, "level": LEVEL, "emissive_intensity": EMISSIVE,
          "materials": [], "actors": [], "errors": []}

def package_file(path, suffix):
    return ROOT / "Content" / (path.removeprefix("/Game/") + suffix)

try:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source_map = package_file(LEVEL, ".umap")
    backup = OUT / "Backups" / (source_map.stem + "_before_night_backdrops_" + stamp + ".umap")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_map, backup)
    report["backup"] = str(backup)
    report["backup_sha256"] = hashlib.sha256(backup.read_bytes()).hexdigest()
    materials = {}
    for suffix in ("01a", "02a"):
        source_path = "/Game/RailBridge/Materials/MI_BG_" + suffix
        source = unreal.load_asset(source_path)
        if not source:
            raise RuntimeError("Missing source backdrop " + source_path)
        source_file = package_file(source_path, ".uasset")
        source_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
        name = "MI_CoastalBackdropNight_" + suffix
        dest_path = DEST + "/" + name
        material = unreal.load_asset(dest_path) if unreal.EditorAssetLibrary.does_asset_exist(dest_path) else None
        if not material:
            material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if not material:
            raise RuntimeError("Could not create " + dest_path)
        unreal.MaterialEditingLibrary.set_material_instance_parent(material, source)
        if "Emissive Intensity" not in [str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(source)]:
            raise RuntimeError("Missing emissive parameter on " + source_path)
        # UE 5.8's setter returns false even after applying the value; verify
        # through the getter instead (MaterialEditingLibrary.cpp, line 1485).
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material, "Emissive Intensity", EMISSIVE)
        actual = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, "Emissive Intensity")
        if abs(actual - EMISSIVE) > 1e-6:
            raise RuntimeError("Emissive override did not apply to " + dest_path)
        unreal.MaterialEditingLibrary.update_material_instance(material)
        if not unreal.EditorAssetLibrary.save_loaded_asset(material, False):
            raise RuntimeError("Could not save night backdrop " + dest_path)
        if hashlib.sha256(source_file.read_bytes()).hexdigest() != source_hash:
            raise RuntimeError("Licensed source backdrop changed on disk")
        materials[source_path + "." + source_path.rsplit("/", 1)[-1]] = material
        materials[material.get_path_name()] = material
        report["materials"].append({"source": source_path, "source_sha256": source_hash,
                                    "instance": dest_path, "source_unchanged": True})
    world = unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
    if not world:
        raise RuntimeError("Connected coast map did not load")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in eas.get_all_level_actors():
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            for index, material in enumerate(component.get_materials()):
                replacement = materials.get(material.get_path_name()) if material else None
                if replacement:
                    actor.modify()
                    component.modify()
                    component.set_material(index, replacement)
                    report["actors"].append({"label": actor.get_actor_label(), "slot": index,
                                             "material": replacement.get_path_name()})
    if len(report["actors"]) != 5:
        raise RuntimeError("Expected exactly five connected coastal backdrops; found " + str(len(report["actors"])))
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, LEVEL):
        raise RuntimeError("Could not save connected coast map")
    report["success"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    (OUT / "Night_Backdrop_Correction.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("NIGHT_BACKDROP_CORRECTION " + str(report["success"]))
