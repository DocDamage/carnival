import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT = ROOT / "Saved/WorldExpansion/Root_Inspection.json"
data = {"map": MAP, "levels": [], "errors": []}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError("Could not load the Carnival root map")
    for level in unreal.EditorLevelUtils.get_levels(world):
        package = level.get_path_name().split(":PersistentLevel")[0].split(".")[0]
        entry = {"package": package}
        try:
            streaming = level.get_outer()
            entry["streaming_class"] = streaming.get_class().get_name()
            entry["should_be_loaded"] = streaming.get_editor_property("should_be_loaded")
            entry["should_be_visible"] = streaming.get_editor_property("should_be_visible")
            entry["transform"] = str(streaming.get_level_transform())
        except Exception as exc:
            entry["streaming_error"] = repr(exc)
        data["levels"].append(entry)
except Exception as exc:
    data["errors"].append(repr(exc))
    data["traceback"] = traceback.format_exc()
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    unreal.log("WORLD_EXPANSION_ROOT_INSPECTION_" + ("FAILED" if data["errors"] else "COMPLETE"))
    unreal.SystemLibrary.quit_editor()
