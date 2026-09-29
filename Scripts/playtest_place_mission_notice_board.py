"""Place and exercise the story start at the authored Carnival mansion board.

The actor is first validated in unsaved PIE with the real player interaction
dispatcher. The connected root map is saved only if the in-game action starts
the mission and the focus system selects this notice-board actor.
"""

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
REPORT_PATH = OUT / "NoticeBoard_PIE_Authoring.json"
LIVE_PATH = OUT / "NoticeBoard_PIE_Authoring_Live.json"
BOARD_LABEL = "Sign_Mansion_Carnival_Board"
LETTERING_LABEL = "Sign_Mansion_Carnival_Lettering"
ACTOR_LABEL = "Mission_NoticeBoard_Interaction"
INTERACTION_RADIUS = 190.0
CAPSULE_RADIUS = 42.0
CAPSULE_HALF_HEIGHT = 96.0

OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")

editor_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level_actors = editor_actors.get_all_level_actors()
board = next((actor for actor in level_actors if actor.get_actor_label() == BOARD_LABEL), None)
lettering = next((actor for actor in level_actors if actor.get_actor_label() == LETTERING_LABEL), None)
if not board:
    raise RuntimeError(f"Could not find the authored sign actor {BOARD_LABEL}")

report = {
    "map": MAP,
    "saved_map_modified": False,
    "board_actor": board.get_path_name(),
    "board_location": list(board.get_actor_location().to_tuple()),
    "sign_lettering_actor": lettering.get_path_name() if lettering else None,
    "candidate_approaches": [],
    "success": False,
    "errors": [],
}


def hit_tuple(hit):
    return hit.to_tuple() if hit else None


def trace_floor(x, y, z):
    hit = hit_tuple(unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, z + 250.0),
        unreal.Vector(x, y, z - 550.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    if not hit or not hit[0] or hit[7].z < 0.65:
        return None
    return {"point": hit[5], "normal": hit[7], "actor": hit[9].get_actor_label() if hit[9] else None}


def static_capsule_clear(position):
    hit = hit_tuple(unreal.SystemLibrary.capsule_trace_single(
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
    return not bool(hit and hit[0]), hit


center = board.get_actor_location()
board_rotation = board.get_actor_rotation()
yaw_radians = math.radians(board_rotation.yaw)
axis_x = unreal.Vector(math.cos(yaw_radians), math.sin(yaw_radians), 0.0)
axis_y = unreal.Vector(-math.sin(yaw_radians), math.cos(yaw_radians), 0.0)
lettering_forward = lettering.get_actor_forward_vector() if lettering else board.get_actor_forward_vector()
bounds_origin, bounds_extent = board.get_actor_bounds(False)
existing_actor = next((actor for actor in level_actors if actor.get_actor_label() == ACTOR_LABEL), None)
selected = None

if existing_actor:
    selected = {
        "actor_location": existing_actor.get_actor_location(),
        "player_location": existing_actor.get_actor_location() + unreal.Vector(0.0, 0.0, 0.0),
        "direction": unreal.Vector(1.0, 0.0, 0.0),
        "floor_actor": "existing placement",
        "lettering_facing_score": 0.0,
        "source": "existing actor",
    }
else:
    directions = [
        ("local_x_positive", axis_x, bounds_extent.x),
        ("local_x_negative", axis_x * -1.0, bounds_extent.x),
        ("local_y_positive", axis_y, bounds_extent.y),
        ("local_y_negative", axis_y * -1.0, bounds_extent.y),
    ]
    for name, direction, extent in directions:
        # Put the interaction sphere just outside the sign's collision bounds,
        # with a standing position farther outward so the sign cannot occlude
        # the prompt's visibility trace.
        actor_xy = center + direction * (extent + 95.0)
        stand_xy = actor_xy + direction * 135.0
        actor_floor = trace_floor(actor_xy.x, actor_xy.y, center.z)
        stand_floor = trace_floor(stand_xy.x, stand_xy.y, center.z)
        item = {
            "name": name,
            "actor_xy": [actor_xy.x, actor_xy.y],
            "player_xy": [stand_xy.x, stand_xy.y],
            "actor_floor": actor_floor["actor"] if actor_floor else None,
            "player_floor": stand_floor["actor"] if stand_floor else None,
            "capsule_clear": False,
            "visibility_clear": False,
            "lettering_facing_score": direction.x * lettering_forward.x + direction.y * lettering_forward.y,
        }
        if not actor_floor or not stand_floor:
            item["rejection"] = "missing walkable floor"
            report["candidate_approaches"].append(item)
            continue
        actor_position = actor_floor["point"] + unreal.Vector(0.0, 0.0, CAPSULE_HALF_HEIGHT + 2.0)
        player_position = stand_floor["point"] + unreal.Vector(0.0, 0.0, CAPSULE_HALF_HEIGHT + 2.0)
        capsule_clear, capsule_hit = static_capsule_clear(player_position)
        item["capsule_clear"] = capsule_clear
        if not capsule_clear:
            item["capsule_blocker"] = capsule_hit[9].get_actor_label() if capsule_hit and capsule_hit[9] else None
        sight_hit = hit_tuple(unreal.SystemLibrary.line_trace_single(
            world,
            player_position + unreal.Vector(0.0, 0.0, 50.0),
            actor_position + unreal.Vector(0.0, 0.0, 40.0),
            unreal.TraceTypeQuery.ECC_VISIBILITY,
            False,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        ))
        item["visibility_clear"] = not bool(sight_hit and sight_hit[0])
        if sight_hit and sight_hit[0]:
            item["visibility_blocker"] = sight_hit[9].get_actor_label() if sight_hit[9] else None
        item["actor_location"] = list(actor_position.to_tuple())
        item["player_location"] = list(player_position.to_tuple())
        report["candidate_approaches"].append(item)
        if capsule_clear and item["visibility_clear"]:
            choice = {
                "actor_location": actor_position,
                "player_location": player_position,
                "direction": direction,
                "floor_actor": stand_floor["actor"],
                "lettering_facing_score": item["lettering_facing_score"],
                "source": name,
            }
            if not selected or choice["lettering_facing_score"] > selected["lettering_facing_score"]:
                selected = choice

if not selected:
    raise RuntimeError("No clear standing position was found in front of the Carnival mansion board")

interaction_class = getattr(unreal, "CarnivalMissionInteractionActor", None)
if not interaction_class:
    interaction_class = unreal.load_class(None, "/Script/CarnivalGame.CarnivalMissionInteractionActor")
if not interaction_class:
    raise RuntimeError("CarnivalMissionInteractionActor is not exposed by the loaded game module")
interaction_enum = getattr(unreal, "CarnivalMissionInteraction", None)
if not interaction_enum or not hasattr(interaction_enum, "NOTICE_BOARD"):
    raise RuntimeError("ECarnivalMissionInteraction.NOTICE_BOARD is not exposed to Unreal Python")

created_new = existing_actor is None
if existing_actor:
    interaction = existing_actor
else:
    interaction = editor_actors.spawn_actor_from_class(
        interaction_class,
        selected["actor_location"],
        unreal.Rotator(pitch=0.0, yaw=board_rotation.yaw, roll=0.0),
    )
if not interaction:
    raise RuntimeError("Could not spawn the mission notice-board interaction actor")
interaction.set_actor_label(ACTOR_LABEL)
interaction.set_folder_path("Mission/Story Start")
interaction.set_actor_location(selected["actor_location"], False, True)
interaction.set_editor_property("interaction", interaction_enum.NOTICE_BOARD)
interaction.set_editor_property("interaction_radius", INTERACTION_RADIUS)
interaction.set_editor_property(
    "accepted_feedback",
    unreal.Text("Investigation started. Follow the coastal road to the mansion."),
)
report.update({
    "actor": interaction.get_path_name(),
    "actor_class": interaction.get_class().get_name(),
    "placement_source": selected["source"],
    "interaction_location": list(interaction.get_actor_location().to_tuple()),
    "player_approach": list(selected["player_location"].to_tuple()),
    "interaction_radius_cm": INTERACTION_RADIUS,
    "interaction_kind": "NOTICE_BOARD",
    "accepted_feedback": "Investigation started. Follow the coastal road to the mansion.",
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
    saved_actor = next((actor for actor in editor_actors.get_all_level_actors()
                        if actor.get_actor_label() == ACTOR_LABEL), None)
    if report["success"]:
        if not saved_actor:
            report["success"] = False
            report["errors"].append("The validated actor did not return to the editor world after PIE")
        else:
            backup_dir = OUT / "Backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / f"LV_Carnival.before_notice_board_{time.strftime('%Y%m%d_%H%M%S')}.umap"
            shutil.copy2(MAP_FILE, backup)
            if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
                report["success"] = False
                report["errors"].append("The map save call returned false")
            else:
                report["saved_map_modified"] = True
                report["backup"] = str(backup)
                report["saved_actor"] = saved_actor.get_path_name()
    elif created_new and saved_actor:
        editor_actors.destroy_actor(saved_actor)
        report["temporary_actor_removed_after_failed_acceptance"] = True
    write_report()
    write_live()
    unreal.log("MISSION_NOTICE_BOARD_AUTHORING " + json.dumps({
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
            game = unreal.EditorLevelLibrary.get_game_world()
            if not game:
                save_verified_actor()
            elif time.monotonic() > state["deadline"]:
                report["success"] = False
                report["errors"].append("PIE did not end before the authoring timeout")
                save_verified_actor()
            return
        if time.monotonic() > state["deadline"]:
            finish("Timed out while waiting for the PIE player")
            return
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        if state["phase"] == "wait_pie":
            player = unreal.GameplayStatics.get_player_pawn(game, 0)
            if not player:
                return
            pie_interactions = unreal.GameplayStatics.get_all_actors_of_class(
                game, interaction_class
            )
            actor = next((item for item in pie_interactions if item.get_actor_label() == ACTOR_LABEL), None)
            if not actor:
                finish("The placed interaction actor did not copy into the PIE world")
                return
            player.get_movement_component().stop_movement_immediately()
            player.set_actor_location(state["approach"], False, True)
            to_board = state["interaction"].get_actor_location() - state["approach"]
            player.set_actor_rotation(unreal.Rotator(
                pitch=0.0, yaw=math.degrees(math.atan2(to_board.y, to_board.x)), roll=0.0
            ), True)
            focus = player.find_nearby_mission_interaction()
            report["player_class"] = player.get_class().get_name()
            report["focused_actor_before_interaction"] = focus.get_actor_label() if focus else None
            report["prompt_before_interaction"] = str(actor.get_prompt_text())
            report["can_interact_before"] = actor.can_interact(player)
            report["floor_supported_player_location"] = list(player.get_actor_location().to_tuple())
            if focus != actor or not report["can_interact_before"]:
                finish("The notice board did not win interaction focus from its clear player approach")
                return
            state["player"] = player
            state["interaction"] = actor
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
            report["can_interact_after"] = actor.can_interact(player)
            report["focused_actor_after_interaction"] = (
                player.find_nearby_mission_interaction().get_actor_label()
                if player.find_nearby_mission_interaction() else None
            )
            report["success"] = (
                not report["can_interact_after"]
                and report["focused_actor_after_interaction"] is None
            )
            if not report["success"]:
                finish("The native context-interaction call did not advance the notice board out of focus")
                return
            report["mission_start_verified"] = True
            finish()
    except Exception:
        finish(traceback.format_exc())
    finally:
        state["busy"] = False


write_report()
write_live()
level_editor.editor_request_begin_play()
handle = unreal.register_slate_post_tick_callback(tick)
