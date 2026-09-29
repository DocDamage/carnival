"""Read-only verification that the accepted notice-board actor persisted."""

import json
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT = ROOT / "Saved/MissionAuthoring/NoticeBoard_SavedMap_Verification.json"
ACTOR_LABEL = "Mission_NoticeBoard_Interaction"
BOARD_LABEL = "Sign_Mansion_Carnival_Board"

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
    interaction = next((actor for actor in actors if actor.get_actor_label() == ACTOR_LABEL), None)
    board = next((actor for actor in actors if actor.get_actor_label() == BOARD_LABEL), None)
    result["loaded_world"] = world.get_path_name()
    result["level_actor_count"] = len(actors)
    result["board_actor_found"] = board is not None
    result["actor_found"] = interaction is not None
    if interaction:
        result.update({
            "actor_path": interaction.get_path_name(),
            "actor_class": interaction.get_class().get_name(),
            "location": list(interaction.get_actor_location().to_tuple()),
            "interaction": str(interaction.get_editor_property("interaction")),
            "interaction_radius_cm": interaction.get_editor_property("interaction_radius"),
            "prompt_override": str(interaction.get_editor_property("prompt_override")),
            "resolved_prompt": str(interaction.get_prompt_text()),
            "accepted_feedback": str(interaction.get_editor_property("accepted_feedback")),
        })
    result["success"] = bool(
        board and interaction
        and interaction.get_class().get_name() == "CarnivalMissionInteractionActor"
        and interaction.get_editor_property("interaction_radius") == 190.0
        and "missing-worker investigation" in str(interaction.get_prompt_text())
    )
    if not result["success"]:
        result["errors"].append("Saved map is missing the configured notice-board interaction actor")
except Exception:
    result["errors"].append(traceback.format_exc())

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("NOTICE_BOARD_SAVED_MAP_VERIFICATION " + json.dumps(result))
if not result["success"]:
    raise RuntimeError("Notice-board saved-map verification failed")
