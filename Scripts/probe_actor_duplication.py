import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\IndustrialHospital\Actor_Duplication_Probe.json")
SOURCE = "/Game/IndustrialSlums/Levels/L_Night"
DEST = "/Game/Carnival/World/Levels/L_IndustrialSlumsDupProbe"
report = {}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(SOURCE)
    report["world"] = world.get_path_name()
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    chosen = [a for a in actors if a.get_class().get_name() == "StaticMeshActor"][:8]
    report["chosen"] = len(chosen)
    report["classes"] = [a.get_class().get_name() for a in chosen]
    report["cast_available"] = hasattr(unreal.Actor, "cast")
    casted = [unreal.Actor.cast(a) for a in chosen]
    report["cast_types"] = [str(type(a)) for a in casted]
    streaming = unreal.EditorLevelUtils.add_level_to_world(world, DEST, unreal.LevelStreamingAlwaysLoaded)
    report["streaming"] = streaming.get_path_name() if streaming else None
    unreal.EditorLevelUtils.make_level_current(streaming)
    duplicates = subsystem.duplicate_actors(casted, world)
    report["duplicates"] = len(duplicates) if duplicates is not None else None
    report["duplicate_levels"] = [a.get_level().get_path_name() for a in duplicates] if duplicates else []
except Exception as exc:
    report["error"] = repr(exc)
    report["traceback"] = traceback.format_exc()
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_ACTOR_DUPLICATION_PROBE_SAVED")
unreal.SystemLibrary.quit_editor()
