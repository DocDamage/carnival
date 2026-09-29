"""Validate and place the mission foyer entry interaction through PIE."""

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
REPORT_PATH = OUT / "MansionEntrance_PIE_Authoring.json"
LIVE_PATH = OUT / "MansionEntrance_PIE_Authoring_Live.json"
BOARD_LABEL = "Mission_NoticeBoard_Interaction"
ACTOR_LABEL = "Mission_MansionEntrance_Interaction"
FOYER_PROBE_LABEL = "Transient_FoyerSearch_StateProbe"
ACTOR_RADIUS = 250.0
CAPSULE_RADIUS = 42.0
CAPSULE_HALF_HEIGHT = 96.0
NOTICE_BOARD_REPORT = OUT / "NoticeBoard_PIE_Authoring.json"

# These are the successful PIE route's inner-door approach and foyer landing.
# The entrance interaction is deliberately on the foyer side of the threshold.
DOOR_APPROACH = unreal.Vector(-70272.62203178785, -86616.14439457298, 932.5410390034085)
FOYER_ROUTE_ANCHOR = unreal.Vector(-70105.17, -86766.43, 915.1290498635826)

OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level_actors = actor_subsystem.get_all_level_actors()
board = next((actor for actor in level_actors if actor.get_actor_label() == BOARD_LABEL), None)
if not board:
    raise RuntimeError(f"Could not find the accepted mission start actor {BOARD_LABEL}")
if not NOTICE_BOARD_REPORT.exists():
    raise RuntimeError(f"Missing accepted board approach report: {NOTICE_BOARD_REPORT}")
board_report = json.loads(NOTICE_BOARD_REPORT.read_text(encoding="utf-8"))
board_approach = unreal.Vector(*board_report["player_approach"])

report = {
    "map": MAP,
    "saved_map_modified": False,
    "placement_side": "foyer side of inner doorway",
    "route_evidence": "Mission_Stair_PIE_Playtest_entry_to_foyer_via_inner_door.json",
    "candidate_approaches": [],
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


direction = FOYER_ROUTE_ANCHOR - DOOR_APPROACH
direction.z = 0.0
direction.normalize()
existing = next((actor for actor in level_actors if actor.get_actor_label() == ACTOR_LABEL), None)
selected = None

if existing:
    existing_location = existing.get_actor_location()
    selected = {
        "actor_location": existing_location,
        "player_location": existing_location + direction * 120.0,
        "source": "existing actor",
    }
else:
    # Shift from the proven foyer landing into the room and check a standing
    # position another 120 cm inward, so the prompt is visible and the capsule
    # does not sit in the inner doorway.
    for actor_offset in (0.0, 60.0, 120.0, 180.0):
        actor_xy = FOYER_ROUTE_ANCHOR + direction * actor_offset
        stand_xy = actor_xy + direction * 120.0
        actor_floor = trace_floor(actor_xy.x, actor_xy.y, FOYER_ROUTE_ANCHOR.z)
        stand_floor = trace_floor(stand_xy.x, stand_xy.y, FOYER_ROUTE_ANCHOR.z)
        item = {
            "foyer_offset_cm": actor_offset,
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
        item["actor_to_player_cm"] = round((player_position - actor_position).length(), 2)
        report["candidate_approaches"].append(item)
        if clear and item["visibility_clear"]:
            selected = {
                "actor_location": actor_position,
                "player_location": player_position,
                "source": f"foyer route anchor + {actor_offset:.0f} cm",
            }
            break

if not selected:
    raise RuntimeError("No capsule-clear, visible entrance interaction approach was found on the foyer side")

interaction_class = getattr(unreal, "CarnivalMissionInteractionActor", None)
if not interaction_class:
    interaction_class = unreal.load_class(None, "/Script/CarnivalGame.CarnivalMissionInteractionActor")
interaction_enum = getattr(unreal, "CarnivalMissionInteraction", None)
if not interaction_class or not interaction_enum or not hasattr(interaction_enum, "MANSION_ENTRANCE"):
    raise RuntimeError("CarnivalMissionInteractionActor or MANSION_ENTRANCE is unavailable to Unreal Python")
if not hasattr(interaction_enum, "FOYER_GLOVE"):
    raise RuntimeError("FOYER_GLOVE is unavailable for the transient mission-state transition probe")

created_new = existing is None
interaction = existing or actor_subsystem.spawn_actor_from_class(
    interaction_class,
    selected["actor_location"],
    unreal.Rotator(pitch=0.0, yaw=math.degrees(math.atan2(direction.y, direction.x)), roll=0.0),
)
if not interaction:
    raise RuntimeError("Could not create the mansion entrance interaction actor")
interaction.set_actor_label(ACTOR_LABEL)
interaction.set_folder_path("Mission/Mansion Entrance")
interaction.set_actor_location(selected["actor_location"], False, True)
interaction.set_editor_property("interaction", interaction_enum.MANSION_ENTRANCE)
interaction.set_editor_property("interaction_radius", ACTOR_RADIUS)
interaction.set_editor_property("prompt_override", unreal.Text("Search the foyer"))
interaction.set_editor_property(
    "accepted_feedback",
    unreal.Text("The foyer is quiet. Search for signs of the missing worker."),
)
foyer_probe = actor_subsystem.spawn_actor_from_class(
    interaction_class,
    selected["actor_location"],
    unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0),
)
if not foyer_probe:
    raise RuntimeError("Could not create the transient foyer-state probe")
foyer_probe.set_actor_label(FOYER_PROBE_LABEL)
foyer_probe.set_folder_path("Mission/Transient Validation")
foyer_probe.set_actor_location(selected["actor_location"], False, True)
foyer_probe.set_editor_property("interaction", interaction_enum.FOYER_GLOVE)
foyer_probe.set_editor_property("interaction_radius", ACTOR_RADIUS)
report.update({
    "actor": interaction.get_path_name(),
    "actor_class": interaction.get_class().get_name(),
    "placement_source": selected["source"],
    "interaction_location": list(interaction.get_actor_location().to_tuple()),
    "player_approach": list(selected["player_location"].to_tuple()),
    "interaction_radius_cm": ACTOR_RADIUS,
    "interaction_kind": "MANSION_ENTRANCE",
    "resolved_prompt": str(interaction.get_prompt_text()),
    "accepted_feedback": "The foyer is quiet. Search for signs of the missing worker.",
    "state_transition_probe": FOYER_PROBE_LABEL,
    "temporary_actor_created": created_new,
})

state = {
    "phase": "wait_pie",
    "busy": False,
    "started": time.monotonic(),
    "deadline": time.monotonic() + 150.0,
    "interaction": interaction,
    "player": None,
    "approach": selected["player_location"],
    "next_action_time": 0.0,
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
    transient_probe = next((actor for actor in actor_subsystem.get_all_level_actors()
                            if actor.get_actor_label() == FOYER_PROBE_LABEL), None)
    if transient_probe:
        actor_subsystem.destroy_actor(transient_probe)
        report["transient_state_probe_removed"] = True
    saved_actor = next((actor for actor in actor_subsystem.get_all_level_actors()
                        if actor.get_actor_label() == ACTOR_LABEL), None)
    if report["success"]:
        if not saved_actor:
            report["success"] = False
            report["errors"].append("Validated actor did not return to the editor world after PIE")
        else:
            backup_dir = OUT / "Backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / f"LV_Carnival.before_mansion_entrance_{time.strftime('%Y%m%d_%H%M%S')}.umap"
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
    unreal.log("MISSION_ENTRANCE_AUTHORING " + json.dumps({
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
        report["player_class"] = player.get_class().get_name()
        if state["phase"] == "wait_pie":
            pie_actors = unreal.GameplayStatics.get_all_actors_of_class(game, interaction_class)
            board_actor = next((item for item in pie_actors if item.get_actor_label() == BOARD_LABEL), None)
            actor = next((item for item in pie_actors if item.get_actor_label() == ACTOR_LABEL), None)
            if not board_actor or not actor:
                finish("PIE did not contain both the saved mission board and temporary foyer interaction")
                return
            foyer_probe_actor = next((item for item in pie_actors if item.get_actor_label() == FOYER_PROBE_LABEL), None)
            if not foyer_probe_actor:
                finish("PIE did not contain the transient foyer-state probe")
                return
            report["pie_board_found"] = True
            report["pie_entrance_found"] = True
            player.get_movement_component().stop_movement_immediately()
            # Start from the already accepted mission board through the actual
            # player's focus and context interaction path.
            board_location = board_actor.get_actor_location()
            player.set_actor_location(board_approach, False, True)
            direction_to_board = board_location - player.get_actor_location()
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(direction_to_board.y, direction_to_board.x)), roll=0.0
            ), True)
            board_focus = player.find_nearby_mission_interaction()
            report["board_focus_before_start"] = board_focus.get_actor_label() if board_focus else None
            if board_focus != board_actor:
                finish("The saved mission board did not win PIE focus before mission start")
                return
            player.try_context_interact()
            report["mission_board_available_after_start"] = board_actor.can_interact(player)
            report["foyer_probe_available_before_entrance"] = foyer_probe_actor.can_interact(player)
            if report["mission_board_available_after_start"] or report["foyer_probe_available_before_entrance"]:
                finish("Mission board interaction did not leave free play and keep foyer search gated")
                return
            # Verify the entrance stays unavailable outside its radius, then
            # move to the clearance-tested foyer approach for focused interaction.
            far_location = state["approach"] + direction * (ACTOR_RADIUS + 120.0)
            player.set_actor_location(far_location, False, True)
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0,
                yaw=math.degrees(math.atan2(actor.get_actor_location().y - far_location.y,
                                            actor.get_actor_location().x - far_location.x)),
                roll=0.0,
            ), True)
            report["out_of_range_focus"] = player.find_nearby_mission_interaction().get_actor_label() if player.find_nearby_mission_interaction() else None
            if report["out_of_range_focus"] == ACTOR_LABEL:
                finish("Entrance interaction incorrectly remained focused outside its radius")
                return
            player.set_actor_location(state["approach"], False, True)
            to_entrance = actor.get_actor_location() - state["approach"]
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_entrance.y, to_entrance.x)), roll=0.0
            ), True)
            focus = player.find_nearby_mission_interaction()
            report["entrance_available_after_start"] = actor.can_interact(player)
            report["foyer_probe_available_at_entrance_before_interaction"] = foyer_probe_actor.can_interact(player)
            report["entrance_focus_before_interaction"] = focus.get_actor_label() if focus else None
            report["entrance_prompt_before_interaction"] = str(actor.get_prompt_text())
            report["entrance_can_interact_before"] = actor.can_interact(player)
            report["floor_supported_player_location"] = list(player.get_actor_location().to_tuple())
            if (focus != actor or not actor.can_interact(player)
                    or report["foyer_probe_available_at_entrance_before_interaction"]):
                finish("Foyer interaction did not win PIE focus from its clear standing position")
                return
            state["player"] = player
            state["interaction"] = actor
            state["foyer_probe"] = foyer_probe_actor
            state["phase"] = "interact"
            state["next_action_time"] = time.monotonic() + 0.5
            write_live()
            return
        if state["phase"] == "interact":
            if time.monotonic() < state["next_action_time"]:
                return
            player = state["player"]
            actor = state["interaction"]
            player.try_context_interact()
            report["context_interaction_dispatched"] = True
            report["entrance_can_interact_after"] = actor.can_interact(player)
            report["focus_after_entrance"] = player.find_nearby_mission_interaction().get_actor_label() if player.find_nearby_mission_interaction() else None
            report["foyer_probe_available_after_entrance"] = state["foyer_probe"].can_interact(player)
            report["success"] = (
                report["mission_board_available_after_start"] is False
                and report["entrance_available_after_start"] is True
                and report["foyer_probe_available_before_entrance"] is False
                and not report["entrance_can_interact_after"]
                and report["foyer_probe_available_after_entrance"]
                and report["focus_after_entrance"] == FOYER_PROBE_LABEL
            )
            report["search_foyer_state_verified"] = report["success"]
            if not report["success"]:
                finish("Native entrance interaction did not enable the SearchFoyer action and focus probe")
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
