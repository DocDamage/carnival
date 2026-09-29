"""Validate the first mansion clue with native PIE focus/state transitions."""

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
REPORT_PATH = OUT / "FoyerClue_PIE_Authoring.json"
LIVE_PATH = OUT / "FoyerClue_PIE_Authoring_Live.json"
NOTICE_BOARD_REPORT = OUT / "NoticeBoard_PIE_Authoring.json"
ENTRANCE_REPORT = OUT / "MansionEntrance_PIE_Authoring.json"
BOARD_LABEL = "Mission_NoticeBoard_Interaction"
ENTRANCE_LABEL = "Mission_MansionEntrance_Interaction"
CLUE_LABEL = "Mission_Foyer_Glove_Note"
STUDY_PROBE_LABEL = "Transient_StudySearch_StateProbe"
INTERACTION_RADIUS = 200.0
CAPSULE_RADIUS = 42.0
CAPSULE_HALF_HEIGHT = 96.0
FLOOR_ANCHOR = unreal.Vector(-70105.17, -86766.43, 915.1290498635826)
DOOR_APPROACH = unreal.Vector(-70272.62203178785, -86616.14439457298, 932.5410390034085)

OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")
if not NOTICE_BOARD_REPORT.exists() or not ENTRANCE_REPORT.exists():
    raise RuntimeError("Mission start and entrance PIE evidence must exist before placing the clue")
board_approach = unreal.Vector(*json.loads(NOTICE_BOARD_REPORT.read_text(encoding="utf-8"))["player_approach"])
entrance_data = json.loads(ENTRANCE_REPORT.read_text(encoding="utf-8"))
entrance_approach = unreal.Vector(*entrance_data["player_approach"])

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level_actors = actor_subsystem.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in level_actors}
for required in (BOARD_LABEL, ENTRANCE_LABEL):
    if required not in by_label:
        raise RuntimeError(f"Missing accepted mission actor: {required}")

report = {
    "map": MAP,
    "saved_map_modified": False,
    "clue": "Eli's wet work glove and note",
    "note_text": "The tune is coming from the study. The music room is locked.",
    "foyer_floor_anchor_actor": "SM_InnerFloor92",
    "allowed_adjacent_foyer_floor": "SM_InnerFloor91",
    "candidate_approaches": [],
    "visual_status": "text label only; a glove static mesh is not yet authored",
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


entrance_actor = by_label[ENTRANCE_LABEL]
entrance_location = entrance_actor.get_actor_location()
inward = FLOOR_ANCHOR - DOOR_APPROACH
inward.z = 0.0
inward.normalize()
side = unreal.Vector(-inward.y, inward.x, 0.0)
selected = None
existing = by_label.get(CLUE_LABEL)
if existing:
    clue_position = existing.get_actor_location()
    stand_position = clue_position - inward * 130.0
    selected = {"actor_location": clue_position, "player_location": stand_position, "source": "existing actor"}
else:
    offsets = [(300.0, 0.0), (340.0, 0.0), (380.0, 0.0)]
    for along in (300.0, 340.0, 380.0, 260.0, 420.0):
        for across in (0.0, 110.0, -110.0, 180.0, -180.0):
            if along in (300.0, 340.0, 380.0) and across == 0.0:
                continue
            offsets.append((along, across))
    seen = set()
    for along, across in offsets:
        if (along, across) in seen:
            continue
        seen.add((along, across))
        actor_xy = FLOOR_ANCHOR + inward * along + side * across
        stand_xy = actor_xy - inward * 130.0
        actor_floor = trace_floor(actor_xy.x, actor_xy.y, FLOOR_ANCHOR.z)
        stand_floor = trace_floor(stand_xy.x, stand_xy.y, FLOOR_ANCHOR.z)
        item = {
            "offset_from_foyer_anchor_cm": [along, across],
            "actor_floor": actor_floor["actor"] if actor_floor else None,
            "player_floor": stand_floor["actor"] if stand_floor else None,
            "capsule_clear": False,
            "visibility_clear": False,
        }
        if not actor_floor or not stand_floor:
            item["rejection"] = "missing walkable floor"
            report["candidate_approaches"].append(item)
            continue
        actor_position = actor_floor["point"] + unreal.Vector(0.0, 0.0, CAPSULE_HALF_HEIGHT + 1.0)
        player_position = stand_floor["point"] + unreal.Vector(0.0, 0.0, CAPSULE_HALF_HEIGHT + 1.0)
        clear, blocker = capsule_clear(player_position)
        item["capsule_clear"] = clear
        if not clear:
            item["capsule_blocker"] = blocker[9].get_actor_label() if blocker and blocker[9] else None
        sight = hit_tuple(unreal.SystemLibrary.line_trace_single(
            world,
            player_position + unreal.Vector(0.0, 0.0, 50.0),
            actor_position + unreal.Vector(0.0, 0.0, 40.0),
            unreal.TraceTypeQuery.ECC_VISIBILITY,
            False,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        ))
        item["visibility_clear"] = not bool(sight and sight[0])
        if sight and sight[0]:
            item["visibility_blocker"] = sight[9].get_actor_label() if sight[9] else None
        item["actor_location"] = list(actor_position.to_tuple())
        item["player_location"] = list(player_position.to_tuple())
        item["distance_from_entrance_cm"] = round((actor_position - entrance_location).length(), 2)
        report["candidate_approaches"].append(item)
        foyer_floors = {"SM_InnerFloor91", "SM_InnerFloor92"}
        if actor_floor["actor"] in foyer_floors and stand_floor["actor"] in foyer_floors and clear and item["visibility_clear"]:
            selected = {
                "actor_location": actor_position,
                "player_location": player_position,
                "source": f"foyer route anchor + {along:.0f} cm inward, {across:.0f} cm lateral",
            }
            break

if not selected:
    report["success"] = False
    report["errors"].append("No capsule-clear clue approach was found on the tested foyer floor")
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("FOYER_CLUE_CANDIDATES " + json.dumps(report["candidate_approaches"]))
    unreal.SystemLibrary.quit_editor()
    raise RuntimeError("No capsule-clear clue approach was found on the tested foyer floor")

interaction_class = getattr(unreal, "CarnivalMissionInteractionActor", None)
if not interaction_class:
    interaction_class = unreal.load_class(None, "/Script/CarnivalGame.CarnivalMissionInteractionActor")
interaction_enum = getattr(unreal, "CarnivalMissionInteraction", None)
if not interaction_class or not interaction_enum or not hasattr(interaction_enum, "FOYER_GLOVE"):
    raise RuntimeError("CarnivalMissionInteractionActor or FOYER_GLOVE is unavailable to Unreal Python")
if not hasattr(interaction_enum, "STUDY_LOG_AND_KEY"):
    raise RuntimeError("STUDY_LOG_AND_KEY is unavailable for the transient transition probe")

created_new = existing is None
interaction = existing or actor_subsystem.spawn_actor_from_class(
    interaction_class,
    selected["actor_location"],
    unreal.Rotator(pitch=0.0, yaw=math.degrees(math.atan2(inward.y, inward.x)), roll=0.0),
)
if not interaction:
    raise RuntimeError("Could not create the foyer clue interaction actor")
interaction.set_actor_label(CLUE_LABEL)
interaction.set_folder_path("Mission/Mansion/Foyer Clue")
interaction.set_actor_location(selected["actor_location"], False, True)
interaction.set_editor_property("interaction", interaction_enum.FOYER_GLOVE)
interaction.set_editor_property("interaction_radius", INTERACTION_RADIUS)
interaction.set_editor_property("prompt_override", unreal.Text("Inspect Eli's wet work glove"))
interaction.set_editor_property("accepted_feedback", unreal.Text(
    "Eli's note reads: \"The tune is coming from the study. The music room is locked.\""
))
interaction.set_editor_property("world_label_text", unreal.Text("Eli's work glove and note"))
interaction.set_editor_property("world_label_offset", unreal.Vector(0.0, 0.0, 18.0))
interaction.set_editor_property("world_label_size", 16.0)

study_probe = actor_subsystem.spawn_actor_from_class(
    interaction_class,
    selected["actor_location"],
    unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0),
)
if not study_probe:
    raise RuntimeError("Could not create the transient study-state probe")
study_probe.set_actor_label(STUDY_PROBE_LABEL)
study_probe.set_folder_path("Mission/Transient Validation")
study_probe.set_actor_location(selected["actor_location"], False, True)
study_probe.set_editor_property("interaction", interaction_enum.STUDY_LOG_AND_KEY)
study_probe.set_editor_property("interaction_radius", INTERACTION_RADIUS)

report.update({
    "actor": interaction.get_path_name(),
    "actor_class": interaction.get_class().get_name(),
    "placement_source": selected["source"],
    "interaction_location": list(interaction.get_actor_location().to_tuple()),
    "player_approach": list(selected["player_location"].to_tuple()),
    "interaction_radius_cm": INTERACTION_RADIUS,
    "interaction_kind": "FOYER_GLOVE",
    "resolved_prompt": str(interaction.get_prompt_text()),
    "accepted_feedback": "Eli's note reads: \"The tune is coming from the study. The music room is locked.\"",
    "world_label_text": "Eli's work glove and note",
    "interaction_mesh": None,
    "transient_state_probe": STUDY_PROBE_LABEL,
    "temporary_actor_created": created_new,
})

state = {
    "phase": "wait_pie",
    "busy": False,
    "started": time.monotonic(),
    "deadline": time.monotonic() + 150.0,
    "approach": selected["player_location"],
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
                  if actor.get_actor_label() == STUDY_PROBE_LABEL), None)
    if probe:
        actor_subsystem.destroy_actor(probe)
        report["transient_state_probe_removed"] = True
    saved_actor = next((actor for actor in actor_subsystem.get_all_level_actors()
                        if actor.get_actor_label() == CLUE_LABEL), None)
    if report["success"]:
        if not saved_actor:
            report["success"] = False
            report["errors"].append("Validated clue actor did not return to the editor world after PIE")
        else:
            backup_dir = OUT / "Backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / f"LV_Carnival.before_foyer_clue_{time.strftime('%Y%m%d_%H%M%S')}.umap"
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
    unreal.log("FOYER_CLUE_AUTHORING " + json.dumps({
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
            finish("Timed out while waiting for the PIE player")
            return
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        player = unreal.GameplayStatics.get_player_pawn(game, 0)
        if not player:
            return
        pie_actors = unreal.GameplayStatics.get_all_actors_of_class(game, interaction_class)
        by_label = {actor.get_actor_label(): actor for actor in pie_actors}
        board_actor = by_label.get(BOARD_LABEL)
        entrance = by_label.get(ENTRANCE_LABEL)
        clue = by_label.get(CLUE_LABEL)
        study_probe_actor = by_label.get(STUDY_PROBE_LABEL)
        if not all((board_actor, entrance, clue, study_probe_actor)):
            finish("PIE did not contain the accepted board, entrance, clue, and study-state probe")
            return

        if state["phase"] == "wait_pie":
            player.get_movement_component().stop_movement_immediately()
            player.set_actor_location(board_approach, False, True)
            to_board = board_actor.get_actor_location() - board_approach
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_board.y, to_board.x)), roll=0.0
            ), True)
            board_focus = player.find_nearby_mission_interaction()
            report["board_focus_before_start"] = board_focus.get_actor_label() if board_focus else None
            if board_focus != board_actor:
                finish("Saved notice board did not win focus before mission start")
                return
            player.try_context_interact()
            report["board_available_after_start"] = board_actor.can_interact(player)
            if report["board_available_after_start"]:
                finish("Mission board remained available after mission start")
                return

            player.set_actor_location(entrance_approach, False, True)
            to_entrance = entrance.get_actor_location() - entrance_approach
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_entrance.y, to_entrance.x)), roll=0.0
            ), True)
            if player.find_nearby_mission_interaction() != entrance:
                finish("Mansion entrance did not win focus after board activation")
                return
            report["entrance_prompt_in_pie"] = str(entrance.get_prompt_text())
            player.try_context_interact()
            report["entrance_disabled_after_use"] = not entrance.can_interact(player)

            # The next state must expose the clue and keep the study gate shut.
            clue_probe_before = clue.can_interact(player)
            study_probe_before = study_probe_actor.can_interact(player)
            if not report["entrance_disabled_after_use"] or not clue_probe_before or study_probe_before:
                finish("Entrance did not expose only the foyer clue state")
                return

            state["phase"] = "approach_clue"
            write_live()
            return

        if state["phase"] == "approach_clue":
            player.set_actor_location(state["approach"], False, True)
            to_clue = clue.get_actor_location() - state["approach"]
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_clue.y, to_clue.x)), roll=0.0
            ), True)
            report["clue_prompt_in_pie"] = str(clue.get_prompt_text())
            report["clue_can_interact_before"] = clue.can_interact(player)
            report["study_probe_available_before_clue"] = study_probe_actor.can_interact(player)
            focus = player.find_nearby_mission_interaction()
            report["clue_focus_before_interaction"] = focus.get_actor_label() if focus else None
            if focus != clue or not clue.can_interact(player) or report["study_probe_available_before_clue"]:
                finish("Foyer clue did not win focus while study search remained gated")
                return
            state["phase"] = "interact_clue"
            state["player"] = player
            state["clue"] = clue
            state["study_probe"] = study_probe_actor
            state["next_action_time"] = time.monotonic() + 0.5
            write_live()
            return

        if state["phase"] == "interact_clue":
            if time.monotonic() < state["next_action_time"]:
                return
            player = state["player"]
            player.try_context_interact()
            clue = state["clue"]
            probe = state["study_probe"]
            report["native_context_interaction_dispatched"] = True
            report["clue_disabled_after_use"] = not clue.can_interact(player)
            report["study_probe_available_after_clue"] = probe.can_interact(player)
            focus = player.find_nearby_mission_interaction()
            report["focus_after_clue"] = focus.get_actor_label() if focus else None
            report["success"] = (
                report["clue_disabled_after_use"]
                and report["study_probe_available_after_clue"]
                and report["focus_after_clue"] == STUDY_PROBE_LABEL
            )
            report["search_study_state_verified"] = report["success"]
            if not report["success"]:
                finish("Foyer clue interaction did not unlock the SearchStudy transition")
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
