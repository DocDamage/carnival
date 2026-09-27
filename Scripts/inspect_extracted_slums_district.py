import json
from collections import Counter
from pathlib import Path
import unreal

world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Carnival/World/Levels/L_IndustrialSlums_DistrictFinal")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
classes = Counter(a.get_class().get_name() for a in actors)
coords = [a.get_actor_location() for a in actors if a.get_class().get_name() not in {"WorldSettings", "Brush"}]
report = {
    "world": world.get_path_name() if world else None,
    "actor_count": len(actors),
    "classes": dict(classes),
    "bounds_cm": {
        "min": [min(getattr(p, axis) for p in coords) for axis in ("x", "y", "z")],
        "max": [max(getattr(p, axis) for p in coords) for axis in ("x", "y", "z")],
    } if coords else None,
    "examples_outside_crop": [
        {"class": a.get_class().get_name(), "label": a.get_actor_label(), "location": [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z]}
        for a in actors
        if a.get_class().get_name() not in {"WorldSettings", "Brush", "Landscape"}
        and not (-20000 <= a.get_actor_location().x <= -10000 and 0 <= a.get_actor_location().y <= 16000)
    ][:30],
}
Path(r"F:\Carnival\Saved\IndustrialHospital\Slums_District_Inspection.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_DISTRICT_INSPECTED")
unreal.SystemLibrary.quit_editor()
