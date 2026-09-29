"""Read-only reload verification for the mansion foyer clue interaction."""

import json
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT = ROOT / "Saved/MissionAuthoring/FoyerClue_SavedMap_Verification.json"
CLUE_LABEL = "Mission_Foyer_Glove_Note"
ENTRANCE_LABEL = "Mission_MansionEntrance_Interaction"
BOARD_LABEL = "Mission_NoticeBoard_Interaction"
TRANSIENT_LABEL = "Transient_StudySearch_StateProbe"

result = {"map": MAP, "read_only": True, "success": False, "errors": []}

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError(f"Could not load {MAP}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in actors}
    clue = by_label.get(CLUE_LABEL)
    result.update({
        "loaded_world": world.get_path_name(),
        "board_found": BOARD_LABEL in by_label,
        "entrance_found": ENTRANCE_LABEL in by_label,
        "clue_found": clue is not None,
        "transient_probe_absent": TRANSIENT_LABEL not in by_label,
    })
    if clue:
        mesh = clue.get_editor_property("interaction_mesh")
        result.update({
            "actor_path": clue.get_path_name(),
            "actor_class": clue.get_class().get_name(),
            "location": list(clue.get_actor_location().to_tuple()),
            "interaction": str(clue.get_editor_property("interaction")),
            "interaction_radius_cm": clue.get_editor_property("interaction_radius"),
            "prompt_override": str(clue.get_editor_property("prompt_override")),
            "resolved_prompt": str(clue.get_prompt_text()),
            "accepted_feedback": str(clue.get_editor_property("accepted_feedback")),
            "world_label_text": str(clue.get_editor_property("world_label_text")),
            "interaction_mesh": mesh.get_path_name() if mesh else None,
        })
    result["success"] = bool(
        clue and BOARD_LABEL in by_label and ENTRANCE_LABEL in by_label
        and TRANSIENT_LABEL not in by_label
        and clue.get_class().get_name() == "CarnivalMissionInteractionActor"
        and "FOYERGLOVE" in str(clue.get_editor_property("interaction")).replace("_", "").upper()
        and clue.get_editor_property("interaction_radius") == 200.0
        and str(clue.get_prompt_text()) == "Inspect Eli's wet work glove"
        and str(clue.get_editor_property("world_label_text")) == "Eli's work glove and note"
        and str(clue.get_editor_property("accepted_feedback"))
            == 'Eli\'s note reads: "The tune is coming from the study. The music room is locked."'
    )
    if not result["success"]:
        result["errors"].append("Saved map is missing or misconfigured for the foyer clue interaction")
except Exception:
    result["errors"].append(traceback.format_exc())

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("FOYER_CLUE_SAVED_MAP_VERIFICATION " + json.dumps(result))
if not result["success"]:
    raise RuntimeError("Foyer clue saved-map verification failed")
