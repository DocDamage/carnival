"""Validate and place the study log/service-key interaction through PIE."""

import json
import math
import shutil
import time
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
MAP_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
OUT = ROOT / "Saved/MissionAuthoring"
REPORT_PATH = OUT / "StudyLogKey_PIE_Authoring.json"
LIVE_PATH = OUT / "StudyLogKey_PIE_Authoring_Live.json"
BOARD_REPORT = OUT / "NoticeBoard_PIE_Authoring.json"
ENTRANCE_REPORT = OUT / "MansionEntrance_PIE_Authoring.json"
CLUE_REPORT = OUT / "FoyerClue_PIE_Authoring.json"
ROOM_ROUTE_REPORT = ROOT / "Saved/MansionConnection/RoomWalk_PIE_foyer92_to_study_full_path.json"
MAP_LABELS = {
    "board": "Mission_NoticeBoard_Interaction",
    "entrance": "Mission_MansionEntrance_Interaction",
    "clue": "Mission_Foyer_Glove_Note",
    "study": "Mission_Study_Log_ServiceKey",
    "worker_probe": "Transient_WorkerStateProbe",
    "table": "SM_WoodTable2",
}
CAPSULE_RADIUS = 42.0
CAPSULE_HALF_HEIGHT = 96.0
INTERACTION_RADIUS = 240.0
BOOK_PATH = "/Game/Mansion/Mesh/Assets/Books/SM_Book02"
NOTE_TEXT = "The music is behind the locked door. Brass service key is in this drawer."

OUT.mkdir(parents=True, exist_ok=True)
required_reports = (BOARD_REPORT, ENTRANCE_REPORT, CLUE_REPORT, ROOM_ROUTE_REPORT)
if not all(path.exists() for path in required_reports):
    raise RuntimeError("The board, foyer entrance/clue, and tested study route reports are required")
board_approach = unreal.Vector(*json.loads(BOARD_REPORT.read_text(encoding="utf-8"))["player_approach"])
entrance_approach = unreal.Vector(*json.loads(ENTRANCE_REPORT.read_text(encoding="utf-8"))["player_approach"])
clue_approach = unreal.Vector(*json.loads(CLUE_REPORT.read_text(encoding="utf-8"))["player_approach"])
study_approach = unreal.Vector(*json.loads(ROOM_ROUTE_REPORT.read_text(encoding="utf-8"))["goal_approach"])

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor_actors = actor_subsystem.get_all_level_actors()
editor_by_label = {actor.get_actor_label(): actor for actor in editor_actors}
for required in (MAP_LABELS["board"], MAP_LABELS["entrance"], MAP_LABELS["clue"], MAP_LABELS["table"]):
    if required not in editor_by_label:
        raise RuntimeError(f"Missing prerequisite actor or study table: {required}")

report = {
    "map": MAP,
    "saved_map_modified": False,
    "story_item": "Eli's maintenance log and brass service key",
    "note_text": NOTE_TEXT,
    "route_evidence": str(ROOM_ROUTE_REPORT.relative_to(ROOT)),
    "success": False,
    "errors": [],
}


def hit_tuple(hit):
    return hit.to_tuple() if hit else None


def trace_floor(x, y, z):
    data = hit_tuple(unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, z + 250.0),
        unreal.Vector(x, y, z - 550.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    if not data or not data[0] or data[7].z < 0.65:
        return None
    return {"point": data[5], "normal": data[7], "actor": data[9].get_actor_label() if data[9] else None}


def capsule_clear(position):
    data = hit_tuple(unreal.SystemLibrary.capsule_trace_single(
        world,
        position,
        position + unreal.Vector(0.0, 0.0, 0.1),
        CAPSULE_RADIUS,
        CAPSULE_HALF_HEIGHT,
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    return not bool(data and data[0]), data


table = editor_by_label[MAP_LABELS["table"]]
table_origin, table_extent = table.get_actor_bounds(False)
table_top = table_origin.z + table_extent.z
interaction_location = unreal.Vector(table.get_actor_location().x, table.get_actor_location().y, table_top + 2.0)
stand_floor = trace_floor(study_approach.x, study_approach.y, study_approach.z)
if not stand_floor:
    raise RuntimeError("Study route approach has no walkable floor trace")
stand_location = stand_floor["point"] + unreal.Vector(0.0, 0.0, CAPSULE_HALF_HEIGHT + 1.0)
clear, capsule_hit = capsule_clear(stand_location)
sight = hit_tuple(unreal.SystemLibrary.line_trace_single(
    world,
    stand_location + unreal.Vector(0.0, 0.0, 50.0),
    interaction_location + unreal.Vector(0.0, 0.0, 40.0),
    unreal.TraceTypeQuery.ECC_VISIBILITY,
    False,
    [],
    unreal.DrawDebugTrace.NONE,
    True,
))
distance = (stand_location - interaction_location).length()
report["placement_probe"] = {
    "study_table": table.get_actor_label(),
    "study_table_mesh": table.get_components_by_class(unreal.StaticMeshComponent)[0].get_editor_property("static_mesh").get_path_name(),
    "study_table_top_z": table_top,
    "standing_floor_actor": stand_floor["actor"],
    "standing_location": list(stand_location.to_tuple()),
    "interaction_location": list(interaction_location.to_tuple()),
    "player_to_interaction_cm": round(distance, 2),
    "capsule_clear": clear,
    "capsule_blocker": capsule_hit[9].get_actor_label() if capsule_hit and capsule_hit[9] else None,
    "visibility_clear": not bool(sight and sight[0]),
    "visibility_blocker": sight[9].get_actor_label() if sight and sight[0] and sight[9] else None,
}
if not clear or (sight and sight[0]) or distance > INTERACTION_RADIUS:
    raise RuntimeError("Study log/key placement failed capsule, sightline, or focus-radius clearance")

interaction_class = getattr(unreal, "CarnivalMissionInteractionActor", None)
if not interaction_class:
    interaction_class = unreal.load_class(None, "/Script/CarnivalGame.CarnivalMissionInteractionActor")
interaction_enum = getattr(unreal, "CarnivalMissionInteraction", None)
if not interaction_class or not interaction_enum or not hasattr(interaction_enum, "STUDY_LOG_AND_KEY"):
    raise RuntimeError("CarnivalMissionInteractionActor or STUDY_LOG_AND_KEY is unavailable to Unreal Python")
worker_enum = getattr(unreal, "CarnivalMissionInteraction", None)
if not worker_enum or not hasattr(worker_enum, "WORKER"):
    raise RuntimeError("WORKER is unavailable for the transient mission-state transition probe")
book_mesh = unreal.load_asset(BOOK_PATH)
if not book_mesh:
    raise RuntimeError(f"Could not load study-log book mesh {BOOK_PATH}")

existing = editor_by_label.get(MAP_LABELS["study"])
created_new = existing is None
interaction = existing or actor_subsystem.spawn_actor_from_class(
    interaction_class,
    interaction_location,
    unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0),
)
if not interaction:
    raise RuntimeError("Could not create the study log/key interaction")
interaction.set_actor_label(MAP_LABELS["study"])
interaction.set_folder_path("Mission/Mansion/Study Log and Key")
interaction.set_actor_location(interaction_location, False, True)
interaction.set_editor_property("interaction", interaction_enum.STUDY_LOG_AND_KEY)
interaction.set_editor_property("interaction_radius", INTERACTION_RADIUS)
interaction.set_editor_property("prompt_override", unreal.Text("Read Eli's log and take the service key"))
interaction.set_editor_property("accepted_feedback", unreal.Text(
    f'Eli\'s log reads: "{NOTE_TEXT}" You take the service key.'
))
interaction.set_editor_property("interaction_mesh", book_mesh)
interaction.set_editor_property("interaction_mesh_offset", unreal.Vector(0.0, 0.0, 4.0))
interaction.set_editor_property("interaction_mesh_scale", unreal.Vector(1.0, 1.0, 1.0))
interaction.set_editor_property("world_label_text", unreal.Text("Maintenance log and service key"))
interaction.set_editor_property("world_label_offset", unreal.Vector(0.0, 0.0, 42.0))
interaction.set_editor_property("world_label_size", 16.0)

worker_probe = actor_subsystem.spawn_actor_from_class(
    interaction_class,
    interaction_location,
    unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0),
)
if not worker_probe:
    raise RuntimeError("Could not create the transient worker-state probe")
worker_probe.set_actor_label(MAP_LABELS["worker_probe"])
worker_probe.set_folder_path("Mission/Transient Validation")
worker_probe.set_actor_location(interaction_location, False, True)
worker_probe.set_editor_property("interaction", worker_enum.WORKER)
worker_probe.set_editor_property("interaction_radius", INTERACTION_RADIUS)

report.update({
    "actor": interaction.get_path_name(),
    "actor_class": interaction.get_class().get_name(),
    "interaction_location": list(interaction.get_actor_location().to_tuple()),
    "player_approach": list(stand_location.to_tuple()),
    "interaction_radius_cm": INTERACTION_RADIUS,
    "interaction_kind": "STUDY_LOG_AND_KEY",
    "resolved_prompt": str(interaction.get_prompt_text()),
    "accepted_feedback": f'Eli\'s log reads: "{NOTE_TEXT}" You take the service key.',
    "world_label_text": "Maintenance log and service key",
    "interaction_mesh": book_mesh.get_path_name(),
    "transient_state_probe": MAP_LABELS["worker_probe"],
    "temporary_actor_created": created_new,
})

state = {
    "phase": "wait_pie",
    "busy": False,
    "started": time.monotonic(),
    "deadline": time.monotonic() + 180.0,
}


def write_report():
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_live():
    LIVE_PATH.write_text(json.dumps({
        "phase": state["phase"],
        "wall_time_seconds": round(time.monotonic() - state["started"], 2),
        "report": report,
    }, indent=2), encoding="utf-8")


def finish(error=None):
    if error:
        report["errors"].append(error)
        report["success"] = False
    report["pie_elapsed_seconds"] = round(time.monotonic() - state["started"], 2)
    state["phase"] = "ending"
    state["deadline"] = time.monotonic() + 15.0
    write_report()
    write_live()
    level_editor.editor_request_end_play()


def save_verified_actor():
    probe = next((actor for actor in actor_subsystem.get_all_level_actors()
                  if actor.get_actor_label() == MAP_LABELS["worker_probe"]), None)
    if probe:
        actor_subsystem.destroy_actor(probe)
        report["transient_state_probe_removed"] = True
    saved_actor = next((actor for actor in actor_subsystem.get_all_level_actors()
                        if actor.get_actor_label() == MAP_LABELS["study"]), None)
    if report["success"]:
        if not saved_actor:
            report["success"] = False
            report["errors"].append("Validated study actor did not return to the editor world after PIE")
        else:
            backup_dir = OUT / "Backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / f"LV_Carnival.before_study_log_key_{time.strftime('%Y%m%d_%H%M%S')}.umap"
            shutil.copy2(MAP_FILE, backup)
            if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
                report["success"] = False
                report["errors"].append("Map save call returned false")
            else:
                report["saved_map_modified"] = True
                report["backup"] = str(backup)
                report["saved_actor"] = saved_actor.get_path_name()
    elif created_new and saved_actor:
        actor_subsystem.destroy_actor(saved_actor)
        report["temporary_actor_removed_after_failed_acceptance"] = True
    write_report()
    write_live()
    unreal.log("STUDY_LOG_KEY_AUTHORING " + json.dumps({
        "success": report["success"],
        "saved_map_modified": report["saved_map_modified"],
        "actor": report.get("saved_actor"),
        "errors": report["errors"],
    }))
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    if state["busy"]:
        return
    state["busy"] = True
    try:
        if state["phase"] == "ending":
            if not unreal.EditorLevelLibrary.get_game_world():
                save_verified_actor()
            elif time.monotonic() > state["deadline"]:
                report["success"] = False
                report["errors"].append("PIE did not end before authoring timeout")
                save_verified_actor()
            return
        if time.monotonic() > state["deadline"]:
            finish("Timed out waiting for the PIE player")
            return
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        player = unreal.GameplayStatics.get_player_pawn(game, 0)
        if not player:
            return
        pie_actors = unreal.GameplayStatics.get_all_actors_of_class(game, interaction_class)
        actors = {actor.get_actor_label(): actor for actor in pie_actors}
        board = actors.get(MAP_LABELS["board"])
        entrance = actors.get(MAP_LABELS["entrance"])
        clue = actors.get(MAP_LABELS["clue"])
        study = actors.get(MAP_LABELS["study"])
        worker = actors.get(MAP_LABELS["worker_probe"])
        if not all((board, entrance, clue, study, worker)):
            finish("PIE did not contain the board, entrance, clue, study item, and worker-state probe")
            return

        if state["phase"] == "wait_pie":
            player.get_movement_component().stop_movement_immediately()
            player.set_actor_location(board_approach, False, True)
            to_board = board.get_actor_location() - board_approach
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_board.y, to_board.x)), roll=0.0
            ), True)
            if player.find_nearby_mission_interaction() != board:
                finish("Notice board did not win initial focus")
                return
            player.try_context_interact()
            if board.can_interact(player):
                finish("Notice board did not start the mission")
                return

            player.set_actor_location(entrance_approach, False, True)
            to_entrance = entrance.get_actor_location() - entrance_approach
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_entrance.y, to_entrance.x)), roll=0.0
            ), True)
            if player.find_nearby_mission_interaction() != entrance:
                finish("Mansion entrance did not win focus after mission start")
                return
            player.try_context_interact()
            if entrance.can_interact(player) or not clue.can_interact(player):
                finish("Mansion entrance did not expose the foyer clue stage")
                return

            player.set_actor_location(clue_approach, False, True)
            to_clue = clue.get_actor_location() - clue_approach
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_clue.y, to_clue.x)), roll=0.0
            ), True)
            if player.find_nearby_mission_interaction() != clue:
                finish("Foyer clue did not win focus after entering the foyer")
                return
            player.try_context_interact()
            report["clue_disabled_after_use"] = not clue.can_interact(player)
            if not report["clue_disabled_after_use"]:
                finish("Foyer clue remained interactable after context interaction")
                return
            state["phase"] = "approach_study"
            state["player"] = player
            state["study"] = study
            state["worker_probe"] = worker
            write_live()
            return

        if state["phase"] == "approach_study":
            player = state["player"]
            study = state["study"]
            worker = state["worker_probe"]
            player.set_actor_location(stand_location, False, True)
            to_study = study.get_actor_location() - stand_location
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_study.y, to_study.x)), roll=0.0
            ), True)
            focus = player.find_nearby_mission_interaction()
            report["study_prompt_in_pie"] = str(study.get_prompt_text())
            report["study_focus_before_interaction"] = focus.get_actor_label() if focus else None
            report["study_can_interact_before"] = study.can_interact(player)
            report["worker_probe_available_before_study"] = worker.can_interact(player)
            report["physical_book_mesh_loaded"] = True
            if focus != study or not study.can_interact(player) or worker.can_interact(player):
                finish("Study log/key did not win focus while FindWorker remained gated")
                return
            state["phase"] = "interact_study"
            state["next_action_time"] = time.monotonic() + 0.5
            write_live()
            return

        if state["phase"] == "interact_study":
            if time.monotonic() < state["next_action_time"]:
                return
            player = state["player"]
            study = state["study"]
            worker = state["worker_probe"]
            player.try_context_interact()
            report["native_context_interaction_dispatched"] = True
            report["study_disabled_after_use"] = not study.can_interact(player)
            report["worker_probe_available_after_study"] = worker.can_interact(player)
            focus = player.find_nearby_mission_interaction()
            report["focus_after_study"] = focus.get_actor_label() if focus else None
            report["success"] = (
                report["study_disabled_after_use"]
                and report["worker_probe_available_after_study"]
                and report["focus_after_study"] == MAP_LABELS["worker_probe"]
            )
            report["find_worker_state_verified"] = report["success"]
            if not report["success"]:
                finish("Study log/key did not enable the FindWorker state probe")
                return
            finish()
    except Exception:
        finish(traceback.format_exc())
    finally:
        state["busy"] = False


write_report()
write_live()
level_editor.editor_request_begin_play()
unreal.register_slate_post_tick_callback(tick)
