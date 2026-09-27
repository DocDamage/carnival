"""Attach the new industrial route, slums, and explorable hospital to Carnival."""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import sys
import unreal

ROOT = Path(r"F:\Carnival")
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import (
    GATE, HOSPITAL_ARCH_LEVEL, HOSPITAL_EXTERIOR_LEVEL, HOSPITAL_LIGHT_LEVEL,
    HOSPITAL_YAW, MAIN_MAP, ROUTE_LEVEL, ROUTE_WORLD_YAW, SLUM_LEVEL,
    hospital_level_transform, slum_level_transform,
)

OUT = ROOT / "Saved/IndustrialHospital"
OUT.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUT / "World_Connection.json"
MAIN_MAP_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"


def package_file(path):
    return ROOT / ("Content" + path.replace("/Game", "").replace("/", "\\") + ".umap")


def make_transform(location, yaw):
    value = unreal.Transform()
    value.set_editor_property("translation", unreal.Vector(*location))
    value.set_editor_property(
        "rotation",
        unreal.Rotator(pitch=0.0, yaw=float(yaw), roll=0.0).quaternion(),
    )
    value.set_editor_property("scale3d", unreal.Vector(1.0, 1.0, 1.0))
    return value


def connect():
    if not MAIN_MAP_FILE.exists():
        raise FileNotFoundError("Carnival root map package is missing")
    backup_dir = OUT / "Backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"LV_Carnival_before_IndustrialHospital_{stamp}.umap"
    shutil.copy2(MAIN_MAP_FILE, backup)
    built_data = MAIN_MAP_FILE.with_name("LV_Carnival_BuiltData.uasset")
    if built_data.exists():
        shutil.copy2(built_data, backup_dir / f"LV_Carnival_BuiltData_before_IndustrialHospital_{stamp}.uasset")

    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    if not world:
        raise RuntimeError("Could not load Carnival root map")
    hospital_location = hospital_level_transform()
    slum_location, slum_yaw = slum_level_transform()
    placements = [
        (ROUTE_LEVEL, GATE, ROUTE_WORLD_YAW),
        (SLUM_LEVEL, slum_location, slum_yaw),
        (HOSPITAL_EXTERIOR_LEVEL, hospital_location, HOSPITAL_YAW),
        (HOSPITAL_ARCH_LEVEL, hospital_location, HOSPITAL_YAW),
        ("/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_SetDress", hospital_location, HOSPITAL_YAW),
        ("/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_Decal", hospital_location, HOSPITAL_YAW),
        ("/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_VFX", hospital_location, HOSPITAL_YAW),
        ("/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Volume", hospital_location, HOSPITAL_YAW),
        (HOSPITAL_LIGHT_LEVEL, hospital_location, HOSPITAL_YAW),
    ]
    # Earlier construction used a positional Rotator and placed these levels
    # with roll instead of yaw. Remove only this branch's streaming entries,
    # then re-add them with the corrected transforms.
    placement_paths = {path for path, _, _ in placements}
    existing_levels = {}
    for level in unreal.EditorLevelUtils.get_levels(world):
        path = level.get_path_name().split(":PersistentLevel")[0].split(".")[0]
        if path in placement_paths:
            existing_levels[path] = level
    replaced = []
    for path, level in existing_levels.items():
        if not unreal.EditorLevelUtils.remove_level_from_world(level):
            raise RuntimeError("Could not replace incorrectly rotated branch level " + path)
        replaced.append(path)

    connected = []
    for path, location, yaw in placements:
        if not package_file(path).exists():
            raise FileNotFoundError("Required connected level is missing: " + path)
        streaming = unreal.EditorLevelUtils.add_level_to_world_with_transform(
            world, path, unreal.LevelStreamingAlwaysLoaded, make_transform(location, yaw)
        )
        if not streaming:
            raise RuntimeError("Could not attach level " + path)
        streaming.set_editor_property("should_be_loaded", True)
        streaming.set_editor_property("should_be_visible", True)
        connected.append(path)

    # add_level_to_world_with_transform switches the active level to the last
    # sublevel it added. save_current_level() would therefore save that
    # sublevel instead of the Carnival persistent world. Save the actual root
    # UWorld explicitly so its streaming-level references persist.
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAIN_MAP):
        raise RuntimeError("Could not save Carnival root map with the connected industrial branch")
    saved_hash = hashlib.sha256(MAIN_MAP_FILE.read_bytes()).hexdigest()
    backup_hash = hashlib.sha256(backup.read_bytes()).hexdigest()
    if saved_hash == backup_hash:
        raise RuntimeError("Carnival root map did not change after adding the streaming levels")
    return {
        "phase": "complete",
        "main_map": MAIN_MAP,
        "main_map_backup": str(backup),
        "main_map_backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
        "main_map_saved_sha256": saved_hash,
        "replaced_levels": replaced,
        "connected_levels": connected,
        "rotator_arguments": {"pitch": 0.0, "yaw": "configured per route", "roll": 0.0},
        "route_transform": {"location": GATE, "yaw": ROUTE_WORLD_YAW},
        "slum_transform": {"location": slum_location, "yaw": slum_yaw},
        "hospital_transform": {"location": hospital_location, "yaw": HOSPITAL_YAW},
    }


try:
    report = connect()
except Exception as exc:
    report = {"phase": "failed", "error": repr(exc), "traceback": traceback.format_exc()}
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_HOSPITAL_WORLD_CONNECTION_" + report["phase"].upper())
unreal.SystemLibrary.quit_editor()
