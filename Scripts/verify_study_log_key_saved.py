"""Read-only reload verification for the mansion study log/key interaction."""

import json
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT = ROOT / "Saved/MissionAuthoring/StudyLogKey_SavedMap_Verification.json"
STUDY_LABEL = "Mission_Study_Log_ServiceKey"
BOARD_LABEL = "Mission_NoticeBoard_Interaction"
ENTRANCE_LABEL = "Mission_MansionEntrance_Interaction"
CLUE_LABEL = "Mission_Foyer_Glove_Note"
TRANSIENT_LABEL = "Transient_WorkerStateProbe"
BOOK_PATH = "/Game/Mansion/Mesh/Assets/Books/SM_Book02"
NOTE_TEXT = "The music is behind the locked door. Brass service key is in this drawer."

result = {"map": MAP, "read_only": True, "success": False, "errors": []}

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not world:
        raise RuntimeError(f"Could not load {MAP}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in actors}
    study = by_label.get(STUDY_LABEL)
    result.update({
        "loaded_world": world.get_path_name(),
        "board_found": BOARD_LABEL in by_label,
        "entrance_found": ENTRANCE_LABEL in by_label,
        "clue_found": CLUE_LABEL in by_label,
        "study_found": study is not None,
        "transient_probe_absent": TRANSIENT_LABEL not in by_label,
    })
    if study:
        mesh = study.get_editor_property("interaction_mesh")
        result.update({
            "actor_path": study.get_path_name(),
            "actor_class": study.get_class().get_name(),
            "location": list(study.get_actor_location().to_tuple()),
            "interaction": str(study.get_editor_property("interaction")),
            "interaction_radius_cm": study.get_editor_property("interaction_radius"),
            "prompt_override": str(study.get_editor_property("prompt_override")),
            "resolved_prompt": str(study.get_prompt_text()),
            "accepted_feedback": str(study.get_editor_property("accepted_feedback")),
            "world_label_text": str(study.get_editor_property("world_label_text")),
            "interaction_mesh": mesh.get_path_name() if mesh else None,
        })
    result["success"] = bool(
        study and all(label in by_label for label in (BOARD_LABEL, ENTRANCE_LABEL, CLUE_LABEL))
        and TRANSIENT_LABEL not in by_label
        and study.get_class().get_name() == "CarnivalMissionInteractionActor"
        and "STUDYLOGANDKEY" in str(study.get_editor_property("interaction")).replace("_", "").upper()
        and study.get_editor_property("interaction_radius") == 240.0
        and str(study.get_prompt_text()) == "Read Eli's log and take the service key"
        and str(study.get_editor_property("accepted_feedback"))
            == f'Eli\'s log reads: "{NOTE_TEXT}" You take the service key.'
        and mesh and mesh.get_path_name() == BOOK_PATH + ".SM_Book02"
    )
    if not result["success"]:
        result["errors"].append("Saved map is missing or misconfigured for the study log/key interaction")
except Exception:
    result["errors"].append(traceback.format_exc())

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("STUDY_LOG_KEY_SAVED_MAP_VERIFICATION " + json.dumps(result))
if not result["success"]:
    raise RuntimeError("Study log/key saved-map verification failed")
