"""Inspect map-level ownership and nested vendor sublevels for expansion maps."""
import json
import traceback
from collections import Counter
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
CASES = {
    "north_docks": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout",
    "east_docks": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksEast",
    "prison": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison",
    "lab_a": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabA",
    "lab_b": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB",
    "sewers": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers",
    "atlantis": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Atlantis",
    "shipwreck": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck",
    "connectors": "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout",
}
OUT = ROOT / "Saved/WorldExpansion/Map_Content_Inspection.json"
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
data = {"maps": [], "errors": []}
try:
    for key, package in CASES.items():
        world = unreal.EditorLoadingAndSavingUtils.load_map(package)
        if not world:
            raise RuntimeError("Could not load " + package)
        row = {"key": key, "package": package, "levels": []}
        for level in unreal.EditorLevelUtils.get_levels(world):
            level_row = {"package": level.get_path_name().split(":PersistentLevel")[0].split(".")[0]}
            try:
                actors = list(level.get_editor_property("actors"))
                level_row["actor_count"] = len([a for a in actors if a])
                level_row["class_counts"] = dict(Counter(a.get_class().get_name() for a in actors if a))
                level_row["actor_labels"] = [a.get_actor_label() for a in actors if a][:35]
            except Exception as exc:
                level_row["actor_error"] = repr(exc)
            row["levels"].append(level_row)
        row["editor_actor_count"] = len(eas.get_all_level_actors())
        data["maps"].append(row)
except Exception as exc:
    data["errors"].append(repr(exc))
    data["traceback"] = traceback.format_exc()
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    unreal.log("WORLD_EXPANSION_MAP_CONTENT_INSPECTION_" + ("FAILED" if data["errors"] else "COMPLETE"))
    unreal.SystemLibrary.quit_editor()
