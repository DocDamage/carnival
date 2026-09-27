import json
from collections import Counter
from pathlib import Path
import unreal

PATH = "/Game/IndustrialSlums/Levels/L_Showcase"
world = unreal.EditorLoadingAndSavingUtils.load_map(PATH)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()
result = {
    "map": PATH,
    "levels": [level.get_path_name() for level in unreal.EditorLevelUtils.get_levels(world)],
    "actor_count": len(actors),
    "classes": dict(Counter(actor.get_class().get_name() for actor in actors)),
    "actors": [],
}
for actor in actors:
    loc = actor.get_actor_location()
    detail = {"label": actor.get_actor_label(), "class": actor.get_class().get_name(),
              "location": loc.to_tuple(), "level": actor.get_level().get_path_name()}
    try:
        origin, extent = actor.get_actor_bounds(False, True)
        detail["bounds"] = {"center": origin.to_tuple(), "extent": extent.to_tuple()}
    except Exception:
        pass
    result["actors"].append(detail)
Path(r"F:\Carnival\Saved\IndustrialHospital\Slums_Showcase_Inspection.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)
unreal.log(f"INDUSTRIAL_SLUMS_SHOWCASE actors={len(actors)} levels={len(result['levels'])}")
