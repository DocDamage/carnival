import json
import unreal
from pathlib import Path

out = Path(r"F:\Carnival\Saved\IndustrialHospital\Transfer_Types.json")
methods = [
    unreal.EditorLevelUtils.move_actors_to_level,
    unreal.EditorActorSubsystem.duplicate_actors,
    unreal.EditorActorSubsystem.get_all_level_actors,
    unreal.EditorLevelLibrary.get_all_level_actors,
]
rows = []
for method in methods:
    rows.append({"name": str(method), "doc": getattr(method, "__doc__", None), "dir": [x for x in dir(method) if not x.startswith("_")]})
rows.append({"array_related": [x for x in dir(unreal) if "Array" in x or "Actor" in x and "Subsystem" in x]})
rows.append({"level_utils": [x for x in dir(unreal.EditorLevelUtils) if "actor" in x.lower() or "level" in x.lower() or "copy" in x.lower()]})
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_TRANSFER_TYPES_SAVED")
unreal.SystemLibrary.quit_editor()
