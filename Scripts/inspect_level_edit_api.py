import json
import unreal
from pathlib import Path

names = [
    "EditorLevelUtils", "EditorLevelLibrary", "EditorAssetLibrary",
    "EditorActorSubsystem", "AssetTools", "LevelStreamingAlwaysLoaded",
]
result = {}
for name in names:
    obj = getattr(unreal, name, None)
    if obj is None:
        result[name] = None
        continue
    methods = {}
    for member in dir(obj):
        if any(term in member.lower() for term in (
            "level", "actor", "copy", "paste", "new", "duplicate", "save", "load"
        )):
            value = getattr(obj, member, None)
            methods[member] = getattr(value, "__doc__", None)
    result[name] = methods

Path(r"F:\Carnival\Saved\IndustrialHospital\Level_Edit_API.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)
unreal.log("INDUSTRIAL_HOSPITAL_LEVEL_EDIT_API_SAVED")
