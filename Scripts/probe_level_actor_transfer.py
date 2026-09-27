import hashlib
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Level_Transfer_Probe.json"
SOURCE = "/Game/IndustrialSlums/Levels/L_Night"
DEST = "/Game/Carnival/World/Levels/L_IndustrialSlumsMoveProbe"
DEST_FILE = ROOT / "Content/Carnival/World/Levels/L_IndustrialSlumsMoveProbe.umap"
report = {"source": SOURCE, "destination": DEST}

try:
    if not DEST_FILE.exists():
        assert unreal.EditorLevelLibrary.new_level(DEST)
        assert unreal.EditorLevelLibrary.save_current_level()
    world = unreal.EditorLoadingAndSavingUtils.load_map(SOURCE)
    source_path = ROOT / "Content/IndustrialSlums/Levels/L_Night.umap"
    report["source_sha_before"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    selected = next(a for a in actors if a.get_class().get_name() == "StaticMeshActor")
    report["selected_actor"] = selected.get_actor_label()
    report["selected_world"] = selected.get_level().get_path_name()
    streaming = unreal.EditorLevelUtils.add_level_to_world(
        world, DEST, unreal.LevelStreamingAlwaysLoaded
    )
    report["streaming_exists"] = bool(streaming)
    if streaming:
        report["streaming_loaded_initial"] = streaming.is_level_loaded()
        report["streaming_visible_initial"] = streaming.is_level_visible()
        streaming.set_editor_property("should_be_loaded", True)
        streaming.set_editor_property("should_be_visible", True)
        try:
            world.flush_level_streaming()
        except Exception as exc:
            report["flush_error"] = repr(exc)
        report["streaming_loaded_after_flush"] = streaming.is_level_loaded()
        report["loaded_level"] = streaming.get_loaded_level().get_path_name() if streaming.get_loaded_level() else None
        unreal.EditorLevelUtils.make_level_current(streaming)
        report["move_count"] = unreal.EditorLevelUtils.move_actors_to_level([selected], streaming, False, False)
        report["selected_world_after"] = selected.get_level().get_path_name()
        report["save_level"] = unreal.EditorLevelLibrary.save_current_level()
    report["source_sha_after"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
except Exception as exc:
    report["error"] = repr(exc)
    report["traceback"] = traceback.format_exc()

OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_SLUMS_LEVEL_TRANSFER_PROBE_SAVED")
unreal.SystemLibrary.quit_editor()
