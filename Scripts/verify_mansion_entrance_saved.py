"""Read-only reload verification for the accepted mansion foyer interaction."""

import json
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT = ROOT / "Saved/MissionAuthoring/MansionEntrance_SavedMap_Verification.json"
ACTOR_LABEL = "Mission_MansionEntrance_Interaction"
BOARD_LABEL = "Mission_NoticeBoard_Interaction"
TRANSIENT_LABEL = "Transient_FoyerSearch_StateProbe"

result = {
    "map": MAP,
    "read_only": True,
    "success": False,
    "errors": [],
}

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError(f"Could not load {MAP}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in actors}
    actor = by_label.get(ACTOR_LABEL)
    board = by_label.get(BOARD_LABEL)
    result["loaded_world"] = world.get_path_name()
    result["actor_found"] = actor is not None
    result["board_found"] = board is not None
    result["transient_probe_absent"] = TRANSIENT_LABEL not in by_label
    if actor:
        result.update({
            "actor_path": actor.get_path_name(),
            "actor_class": actor.get_class().get_name(),
            "location": list(actor.get_actor_location().to_tuple()),
            "interaction": str(actor.get_editor_property("interaction")),
            "interaction_radius_cm": actor.get_editor_property("interaction_radius"),
            "prompt_override": str(actor.get_editor_property("prompt_override")),
            "resolved_prompt": str(actor.get_prompt_text()),
            "accepted_feedback": str(actor.get_editor_property("accepted_feedback")),
        })
    result["success"] = bool(
        actor and board and TRANSIENT_LABEL not in by_label
        and actor.get_class().get_name() == "CarnivalMissionInteractionActor"
        and "MANSIONENTRANCE" in str(actor.get_editor_property("interaction")).replace("_", "").upper()
        and actor.get_editor_property("interaction_radius") == 250.0
        and str(actor.get_prompt_text()) == "Search the foyer"
    )
    if not result["success"]:
        result["errors"].append("Saved map is missing or misconfigured for the foyer entrance interaction")
except Exception:
    result["errors"].append(traceback.format_exc())

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("MANSION_ENTRANCE_SAVED_MAP_VERIFICATION " + json.dumps(result))
if not result["success"]:
    raise RuntimeError("Mansion entrance saved-map verification failed")
