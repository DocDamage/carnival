"""Read-only audit of the connected Carnival streaming levels and transforms."""
import json
import time
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Connected_State.json"
MAIN = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN)
report = {"map": MAIN, "streaming_levels": [], "world_levels": []}

def safe(fn):
    try:
        value = fn()
        if hasattr(value, "get_path_name"):
            return value.get_path_name()
        if hasattr(value, "to_tuple"):
            return list(value.to_tuple())
        return value
    except Exception as exc:
        return "ERROR: " + repr(exc)

def transform_data(value):
    result = {}
    for key in ("translation", "rotation", "scale3d"):
        v = safe(lambda: value.get_editor_property(key))
        result[key] = v
        if key == "rotation" and not isinstance(v, str):
            result[key] = safe(lambda: value.rotator())
    return result

for streaming in world.get_editor_property("streaming_levels"):
    asset = safe(lambda: streaming.get_editor_property("world_asset"))
    loaded = safe(lambda: streaming.is_level_loaded())
    visible = safe(lambda: streaming.is_level_visible())
    row = {
        "asset": asset,
        "loaded": loaded,
        "visible": visible,
        "should_be_loaded": safe(lambda: streaming.get_editor_property("should_be_loaded")),
        "should_be_visible": safe(lambda: streaming.get_editor_property("should_be_visible")),
        "transform": transform_data(streaming.get_editor_property("level_transform")),
    }
    level = streaming.get_loaded_level() if loaded else None
    if level:
        actors = []
        for actor in level.get_editor_property("actors"):
            if not actor:
                continue
            label = actor.get_actor_label()
            cls = actor.get_class().get_name()
            if any(word in label.lower() for word in ("hospital", "slum", "fog", "snow", "facade", "road")) or cls in ("PostProcessVolume", "ExponentialHeightFog", "DirectionalLight"):
                actors.append({"label": label, "class": cls,
            "location": safe(lambda a=actor: a.get_actor_location().to_tuple())})
        row["loaded_level"] = safe(lambda: level.get_path_name())
        row["actor_count"] = len(level.get_editor_property("actors"))
        row["notable_actors"] = actors[:80]
    report["streaming_levels"].append(row)

for level in unreal.EditorLevelUtils.get_levels(world):
    report["world_levels"].append({
        "path": level.get_path_name(),
        "visibility": [
            {"asset": row["asset"], "visible": row["visible"]}
            for row in report["streaming_levels"]
            if row.get("loaded_level", "").startswith(level.get_path_name().split(":PersistentLevel")[0].split(".")[0])
        ],
    })

OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_HOSPITAL_CONNECTED_STATE_SAVED")
unreal.SystemLibrary.quit_editor()
