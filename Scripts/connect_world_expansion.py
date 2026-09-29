"""Attach the authored expansion maps to the established Carnival world."""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAIN_MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
MAIN_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
REPORT_PATH = ROOT / "Saved/WorldExpansion/World_Connection.json"
LEVELS = [
    ("north_docks", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout", (-55000.0, -55000.0, 600.0), 0.0),
    ("prison", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison", (-24829.058923937297, -33605.033443166416, -1037.206), -45.0),
    ("lab_a", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabA", (-42097.962876199206, -7043.716818882417, 600.0), -57.0),
    ("lab_b", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB", (-42524.98929804207, -5651.722409752812, 600.0), 123.0),
    ("east_docks", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksEast", (70000.0, 15000.0, 600.0), 0.0),
    ("sewers", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers", (-27100.0, -12290.0, -1800.0), 0.0),
    ("atlantis", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Atlantis", (-13000.0, -11000.0, -1800.0), 0.0),
    ("shipwreck", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck", (-6033.089, -10010.0, -2108.649), 0.0),
    ("connectors", "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout", (0.0, 0.0, 0.0), 0.0),
]


def package_file(package):
    return ROOT / ("Content" + package.replace("/Game", "").replace("/", "\\") + ".umap")


def transform(location, yaw):
    value = unreal.Transform()
    value.set_editor_property("translation", unreal.Vector(*location))
    value.set_editor_property("rotation", unreal.Rotator(0.0, float(yaw), 0.0).quaternion())
    value.set_editor_property("scale3d", unreal.Vector(1.0, 1.0, 1.0))
    return value


def level_package(level):
    return level.get_path_name().split(":PersistentLevel")[0].split(".")[0]


def connect():
    if not MAIN_FILE.exists():
        raise FileNotFoundError("Carnival root map is missing: " + str(MAIN_FILE))
    for key, package, _location, _yaw in LEVELS:
        if not package_file(package).exists():
            raise FileNotFoundError("Authored region is missing (" + key + "): " + str(package_file(package)))

    backup_dir = ROOT / "Saved/WorldExpansion/Backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / ("LV_Carnival_before_WorldExpansion_" + stamp + ".umap")
    shutil.copy2(MAIN_FILE, backup)
    built_data = MAIN_FILE.with_name("LV_Carnival_BuiltData.uasset")
    built_backup = None
    if built_data.exists():
        built_backup = backup_dir / ("LV_Carnival_BuiltData_before_WorldExpansion_" + stamp + ".uasset")
        shutil.copy2(built_data, built_backup)

    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    if not world:
        raise RuntimeError("Could not load Carnival root map")
    existing = {level_package(level) for level in unreal.EditorLevelUtils.get_levels(world)}
    connected, already_present = [], []
    for key, package, location, yaw in LEVELS:
        if package in existing:
            already_present.append(package)
            continue
        streaming = unreal.EditorLevelUtils.add_level_to_world_with_transform(
            world, package, unreal.LevelStreamingAlwaysLoaded, transform(location, yaw)
        )
        if not streaming:
            raise RuntimeError("Could not stream region into Carnival: " + package)
        streaming.set_editor_property("should_be_loaded", True)
        streaming.set_editor_property("should_be_visible", True)
        connected.append({"key": key, "package": package,
                          "location_cm": list(location), "yaw_deg": yaw})
        existing.add(package)

    # Keep saving the root World explicit: adding a stream level changes the
    # editor's current level to that stream level.
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAIN_MAP):
        raise RuntimeError("Could not save Carnival root map with expansion regions")
    saved_hash = hashlib.sha256(MAIN_FILE.read_bytes()).hexdigest()
    if saved_hash == hashlib.sha256(backup.read_bytes()).hexdigest():
        raise RuntimeError("Carnival root map did not change after level integration")
    return {
        "phase": "complete", "main_map": MAIN_MAP,
        "backup": str(backup), "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
        "built_data_backup": str(built_backup) if built_backup else None,
        "saved_sha256": saved_hash, "connected_levels": connected,
        "already_present": already_present,
        "root_level_packages_after_save": sorted({level_package(level) for level in unreal.EditorLevelUtils.get_levels(world)}),
    }


try:
    report = connect()
except Exception as exc:
    report = {"phase": "failed", "error": repr(exc), "traceback": traceback.format_exc()}
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("WORLD_EXPANSION_CONNECTION_" + report["phase"].upper())
unreal.SystemLibrary.quit_editor()
