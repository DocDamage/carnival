"""Check project-local map duplication without editing the live Carnival map."""
import json
import gc
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Duplication_Probe.json"
SOURCE = "/Game/Docks/VOL2_Powell/Maps/Demonstration"
NAME = "L_WExp_Probe_Docks"
DEST = "/Game/Carnival/World/Levels"
report = {"maps": [], "errors": []}
try:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    source_asset = unreal.load_asset(SOURCE)
    if not source_asset:
        raise RuntimeError("Could not load source map " + SOURCE)
    dest_path = DEST + "/" + NAME
    clone = unreal.load_asset(dest_path)
    if not clone:
        clone = asset_tools.duplicate_asset(NAME, DEST, source_asset)
        if not clone:
            raise RuntimeError("Could not duplicate " + SOURCE)
        if not unreal.EditorAssetLibrary.save_loaded_asset(clone, False):
            raise RuntimeError("Could not save duplicated map " + dest_path)
    source_asset = None
    clone = None
    gc.collect()
    world = unreal.EditorLoadingAndSavingUtils.load_map(dest_path)
    if not world:
        raise RuntimeError("Could not load duplicated map " + dest_path)
    levels = unreal.EditorLevelUtils.get_levels(world)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    report["maps"].append({
        "label": "docks", "source": SOURCE, "clone": dest_path,
        "levels": [level.get_path_name().split(":PersistentLevel")[0].split(".")[0] for level in levels],
        "level_count": len(levels), "visible_actor_count": len(actors),
    })
    report["success"] = True
except Exception as exc:
    report["success"] = False
    report["errors"].append(repr(exc))
    report["traceback"] = traceback.format_exc()
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("WORLD_EXPANSION_DUPLICATION_PROBE_" + ("COMPLETE" if report.get("success") else "FAILED"))
    unreal.SystemLibrary.quit_editor()
