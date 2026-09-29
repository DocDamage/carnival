"""Walk the playable character up and down the placed mansion exterior stairs in PIE."""

import json
import math
import os
import time
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
STAIRS_LABEL = os.environ.get("CARNIVAL_TEST_STAIRS", "SM_OuterStairs10")
ENTRY_APPROACH = os.environ.get("CARNIVAL_TEST_ENTRY_APPROACH", "")
INTERIOR_TARGET = os.environ.get("CARNIVAL_TEST_INTERIOR_TARGET", "")
REPORT_SUFFIX = (
    f"_{INTERIOR_TARGET}"
    if INTERIOR_TARGET
    else "" if STAIRS_LABEL == "SM_OuterStairs10" else f"_{STAIRS_LABEL}"
)
INTERIOR_TARGETS = {
    "door12": {
        "segment": "walk_to_door12_threshold",
        "point": [-70300.44275158, -86170.45519227076, 915.6859069160156],
    },
    "foyer92": {
        "segment": "walk_to_foyer_floor92",
        "point": [-70105.17, -86766.43, 915.1290498635826],
    },
    "entry_to_foyer": {
        "waypoints": [
            {
                "segment": "walk_to_door12_threshold",
                "point": [-70300.44275158, -86170.45519227076, 915.6859069160156],
            },
            {
                "segment": "walk_to_foyer_floor92",
                "point": [-70105.17, -86766.43, 915.1290498635826],
            },
        ],
    },
    "entry_to_inner_door": {
        "waypoints": [
            {
                "segment": "walk_to_door12_threshold",
                "point": [-70300.44275158, -86170.45519227076, 915.6859069160156],
            },
            {
                "segment": "walk_to_inner_door_approach",
                "point": [-70272.62203178785, -86616.14439457298, 932.5410390034085],
            },
        ],
    },
    "entry_to_foyer_via_inner_door": {
        "waypoints": [
            {
                "segment": "walk_to_door12_threshold",
                "point": [-70300.44275158, -86170.45519227076, 915.6859069160156],
            },
            {
                "segment": "walk_to_inner_door_approach",
                "point": [-70272.62203178785, -86616.14439457298, 932.5410390034085],
            },
            {
                "segment": "walk_to_foyer_floor92",
                "point": [-70105.17, -86766.43, 915.1290498635826],
            },
        ],
    },
    "mission_route_roundtrip": {
        "waypoints": [
            {
                "segment": "walk_to_door12_threshold",
                "point": [-70300.44275158, -86170.45519227076, 915.6859069160156],
            },
            {
                "segment": "walk_to_inner_door_approach",
                "point": [-70272.62203178785, -86616.14439457298, 932.5410390034085],
            },
            {
                "segment": "walk_to_foyer_floor92",
                "point": [-70105.17, -86766.43, 915.1290498635826],
            },
        ],
    },
}
REPORT_PATH = ROOT / f"Saved/MansionConnection/Mission_Stair_PIE_Playtest{REPORT_SUFFIX}.json"
LIVE_PATH = ROOT / f"Saved/MansionConnection/Mission_Stair_PIE_Playtest{REPORT_SUFFIX}_Live.json"
report = {
    "map": MAP,
    "saved_map_modified": False,
    "stairs_label": STAIRS_LABEL,
    "entry_approach_mode": ENTRY_APPROACH or None,
    "interior_target_mode": INTERIOR_TARGET or None,
    "segments": [],
}
state = {"phase": "setup", "deadline": time.monotonic() + 120, "busy": False}
report["startup_phase"] = "script_started"
state["setup_poll_count"] = 0


def write_live():
    LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": state["phase"],
        "startup_phase": report.get("startup_phase"),
        "time": time.time(),
        "report": report,
    }
    player = state.get("player")
    if player:
        payload["player_position"] = list(player.get_actor_location().to_tuple())
    LIVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


write_live()
current_world = unreal.EditorLevelLibrary.get_editor_world()
if current_world and current_world.get_name() == "LV_Carnival":
    world = current_world
    report["reused_editor_startup_map"] = True
else:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    report["reused_editor_startup_map"] = False
if not world:
    raise RuntimeError(f"Could not load {MAP}")
report["editor_world_name"] = world.get_name()
report["startup_phase"] = "map_ready"
write_live()

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report["excluded_crowd_spawners"] = []
for actor in list(actor_subsystem.get_all_level_actors()):
    if actor.get_class().get_name() == "MetaHumanMassSpawner":
        report["excluded_crowd_spawners"].append(actor.get_actor_label())
        actor_subsystem.destroy_actor(actor)
report["startup_phase"] = "spawners_removed"
write_live()

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.editor_request_begin_play()
report["startup_phase"] = "pie_requested"
state["deadline"] = time.monotonic() + 120
write_live()


def vlist(value):
    return list(value.to_tuple())


def xy_distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def floor_trace(game, x, y, z):
    hit = unreal.SystemLibrary.line_trace_single(
        game,
        unreal.Vector(x, y, z + 100.0),
        unreal.Vector(x, y, z - 1200.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [state["player"]],
        unreal.DrawDebugTrace.NONE,
        True,
    )
    hit = hit.to_tuple() if hit else None
    if not hit or not hit[0]:
        return None
    return {
        "point": hit[5],
        "normal": hit[7],
        "actor": hit[9].get_actor_label() if hit[9] else None,
    }


def capsule_block_trace(game, player, start, goal, half_height):
    hit = unreal.SystemLibrary.capsule_trace_single(
        game,
        start,
        goal,
        42.0,
        half_height,
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [player],
        unreal.DrawDebugTrace.NONE,
        True,
    )
    hit = hit.to_tuple() if hit else None
    if not hit or not hit[0]:
        return {"blocked": False}
    return {
        "blocked": True,
        "actor": hit[9].get_actor_label() if hit[9] else None,
        "impact_point": vlist(hit[5]) if hit[5] else None,
        "impact_normal": vlist(hit[7]) if hit[7] else None,
    }


def finish(error=None):
    if error:
        report["error"] = error
    report["final_phase"] = state["phase"]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_live()
    levels.editor_request_end_play()
    state.update(phase="exit", deadline=time.monotonic() + 2)


def begin_segment(name, start_floor, goal_floor, start_position=None):
    player = state["player"]
    capsule_height = state["capsule_half_height"]
    start = (
        start_position
        if start_position is not None
        else start_floor["point"] + unreal.Vector(0, 0, capsule_height + 2.0)
    )
    goal = goal_floor["point"] + unreal.Vector(0, 0, capsule_height)
    direction = unreal.Vector(goal.x - start.x, goal.y - start.y, 0)
    distance = math.hypot(direction.x, direction.y)
    direction = direction / max(distance, 1.0)
    yaw = math.degrees(math.atan2(direction.y, direction.x))
    player.get_movement_component().stop_movement_immediately()
    if start_position is None:
        player.set_actor_location(start, False, True)
    player.set_actor_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0), True)
    now = unreal.GameplayStatics.get_time_seconds(state["game"])
    segment = {
        "name": name,
        "success": False,
        "start": vlist(start),
        "goal": vlist(goal),
        "start_floor_actor": start_floor["actor"],
        "goal_floor_actor": goal_floor["actor"],
        "goal_floor_z": goal_floor["point"].z,
        "samples": [],
    }
    report["segments"].append(segment)
    state.update(
        phase=name,
        segment=segment,
        start=start,
        goal=goal,
        direction=direction,
        started=now,
        last_sample=now - 1.0,
        last_progress=now,
        last_distance=distance,
        deadline=time.monotonic() + 12,
    )
    write_live()


def begin_next_return_segment(game, position):
    index = state["return_waypoint_index"]
    waypoints = state["return_waypoints"]
    if index >= len(waypoints):
        report["success"] = True
        finish()
        return
    start_floor = floor_trace(game, position.x, position.y, position.z)
    if not start_floor:
        finish("No floor support at the reached return waypoint")
        return
    waypoint = waypoints[index]
    state["return_waypoint_index"] = index + 1
    begin_segment(waypoint["segment"], start_floor, waypoint["floor"], position)


def tick(_delta):
    if state["busy"]:
        return
    state["busy"] = True
    try:
        if state["phase"] == "exit":
            if time.monotonic() > state["deadline"]:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if time.monotonic() > state["deadline"]:
            finish(f"Timed out during {state['phase']}")
            return

        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            state["setup_poll_count"] += 1
            report["last_pie_poll"] = {
                "game_world": None,
                "poll_count": state["setup_poll_count"],
            }
            if state["setup_poll_count"] % 30 == 0:
                unreal.log(f"MANSION_STAIR_WAIT no_pie_world polls={state['setup_poll_count']}")
                write_live()
            return
        if state["phase"] == "setup":
            player = unreal.GameplayStatics.get_player_pawn(game, 0)
            if not player:
                state["setup_poll_count"] += 1
                try:
                    controller_count = len(
                        unreal.GameplayStatics.get_all_actors_of_class(
                            game, unreal.PlayerController
                        )
                    )
                except Exception:
                    controller_count = None
                report["last_pie_poll"] = {
                    "game_world": game.get_name(),
                    "player_pawn": None,
                    "player_controller_count": controller_count,
                    "poll_count": state["setup_poll_count"],
                }
                if state["setup_poll_count"] % 30 == 0:
                    unreal.log(
                        f"MANSION_STAIR_WAIT no_player_pawn world={game.get_name()} "
                        f"controllers={controller_count} polls={state['setup_poll_count']}"
                    )
                    write_live()
                return
            stairs = next(
                (
                    actor
                    for actor in unreal.GameplayStatics.get_all_actors_of_class(
                        game, unreal.StaticMeshActor
                    )
                    if actor.get_actor_label() == STAIRS_LABEL
                ),
                None,
            )
            if not stairs:
                finish(f"Placed {STAIRS_LABEL} actor not found in PIE")
                return
            capsule = player.get_component_by_class(unreal.CapsuleComponent)
            try:
                half_height = capsule.get_scaled_capsule_half_height() if capsule else 98.2
            except Exception:
                half_height = (
                    float(capsule.get_editor_property("capsule_half_height"))
                    * player.get_actor_scale3d().z
                    if capsule
                    else 98.2
                )
            state.update(game=game, player=player, stairs=stairs, capsule_half_height=half_height)
            report["player_class"] = player.get_class().get_name()
            report["pie_setup"] = "complete"
            write_live()

            # The mesh runs from local Y ~= +11/Z 0 at the bottom to Y ~= -541/Z 206 at the top.
            transform = stairs.get_actor_transform()
            base = transform.transform_location(unreal.Vector(369.0, 120.0, 0.0))
            top = transform.transform_location(unreal.Vector(369.0, -500.0, 190.0))
            base_floor = floor_trace(game, base.x, base.y, base.z)
            top_floor = floor_trace(game, top.x, top.y, top.z)
            report["actor_location"] = vlist(stairs.get_actor_location())
            report["actor_rotation"] = vlist(stairs.get_actor_rotation())
            report["actor_scale"] = vlist(stairs.get_actor_scale3d())
            report["capsule_half_height_cm"] = half_height
            report["base_probe"] = {
                "point": vlist(base),
                "floor": {"point": vlist(base_floor["point"]), "actor": base_floor["actor"]} if base_floor else None,
            }
            report["top_probe"] = {
                "point": vlist(top),
                "floor": {"point": vlist(top_floor["point"]), "actor": top_floor["actor"]} if top_floor else None,
            }
            if not base_floor or not top_floor:
                finish("No floor support at the computed stair base or top")
                return
            state["base_floor"] = base_floor
            state["top_floor"] = top_floor
            target = INTERIOR_TARGETS.get(INTERIOR_TARGET)
            if INTERIOR_TARGET and not target:
                finish(f"Unknown interior target: {INTERIOR_TARGET}")
                return
            if target:
                target_waypoints = target.get("waypoints", [target])
                state["interior_waypoints"] = []
                for waypoint in target_waypoints:
                    target_floor = floor_trace(game, *waypoint["point"])
                    if not target_floor:
                        finish(f"No floor support at {waypoint['segment']}")
                        return
                    state["interior_waypoints"].append(
                        {**waypoint, "floor": target_floor}
                    )
                target_records = [
                    {
                        "name": waypoint["segment"],
                        "point": waypoint["point"],
                        "floor": {
                            "point": vlist(waypoint["floor"]["point"]),
                            "actor": waypoint["floor"]["actor"],
                        },
                    }
                    for waypoint in state["interior_waypoints"]
                ]
                if len(target_records) == 1:
                    report["interior_target"] = target_records[0]
                else:
                    report["interior_targets"] = target_records
                state["interior_waypoint_index"] = 0
            if ENTRY_APPROACH == "front_door":
                approach_floor = floor_trace(game, -69150.0, -85300.0, 697.15625)
                if not approach_floor:
                    finish("No floor support at the front-door approach")
                    return
                report["entry_approach"] = {
                    "point": [-69150.0, -85300.0, 697.15625],
                    "floor": {
                        "point": vlist(approach_floor["point"]),
                        "actor": approach_floor["actor"],
                    },
                }
                state["entry_floor"] = approach_floor
                begin_segment("walk_entry_to_stair", approach_floor, base_floor)
            else:
                begin_segment("walk_up", base_floor, top_floor)
            return

        player = state["player"]
        now = unreal.GameplayStatics.get_time_seconds(game)
        position = player.get_actor_location()
        remaining = xy_distance(position, state["goal"])
        current_floor = None
        segment = state["segment"]
        if now - state["last_sample"] >= 0.5:
            current_floor = floor_trace(game, position.x, position.y, position.z)
            floor_z = current_floor["point"].z if current_floor else None
            state["last_floor_z"] = floor_z
            state["last_floor_actor"] = current_floor["actor"] if current_floor else None
            segment["samples"].append(
                {
                    "seconds": round(now - state["started"], 2),
                    "position": vlist(position),
                    "horizontal_remaining_cm": round(remaining, 1),
                    "floor_z": floor_z,
                    "floor_actor": current_floor["actor"] if current_floor else None,
                    "velocity": vlist(player.get_velocity()),
                }
            )
            state["last_sample"] = now
            write_live()
        floor_z = state.get("last_floor_z")
        if remaining < 80 and floor_z is not None and abs(position.z - floor_z - state["capsule_half_height"]) < 45:
            segment.update(success=True, seconds=round(now - state["started"], 2), finish=vlist(position))
            if state["phase"] == "walk_entry_to_stair":
                landed_floor = floor_trace(game, position.x, position.y, position.z)
                if not landed_floor:
                    finish("No floor support at the actual stair-base approach")
                    return
                begin_segment("walk_up", landed_floor, state["top_floor"], position)
            elif state["phase"] == "walk_up":
                landed_floor = floor_trace(game, position.x, position.y, position.z)
                if not landed_floor:
                    finish("No floor support at the actual stair landing")
                    return
                state["actual_top_floor"] = landed_floor
                state["actual_top_position"] = position
                if INTERIOR_TARGET:
                    waypoint = state["interior_waypoints"][0]
                    begin_segment(
                        waypoint["segment"],
                        landed_floor,
                        waypoint["floor"],
                        position,
                    )
                else:
                    begin_segment("walk_down", landed_floor, state["base_floor"], position)
            elif state["phase"].startswith("walk_to_"):
                next_index = state["interior_waypoint_index"] + 1
                waypoints = state.get("interior_waypoints", [])
                if next_index < len(waypoints):
                    current_floor = floor_trace(game, position.x, position.y, position.z)
                    if not current_floor:
                        finish("No floor support at the reached mansion waypoint")
                        return
                    state["interior_waypoint_index"] = next_index
                    waypoint = waypoints[next_index]
                    begin_segment(
                        waypoint["segment"],
                        current_floor,
                        waypoint["floor"],
                        position,
                    )
                else:
                    if INTERIOR_TARGET == "mission_route_roundtrip":
                        if not state.get("entry_floor"):
                            finish("Round-trip needs the front-door approach start")
                            return
                        state["returning"] = True
                        state["return_waypoints"] = [
                            {"segment": "walk_return_to_inner_door", "floor": state["interior_waypoints"][1]["floor"]},
                            {"segment": "walk_return_to_door12", "floor": state["interior_waypoints"][0]["floor"]},
                            {"segment": "walk_return_to_stair_top", "floor": state["actual_top_floor"]},
                            {"segment": "walk_down", "floor": state["base_floor"]},
                            {"segment": "walk_return_to_front_door", "floor": state["entry_floor"]},
                        ]
                        state["return_waypoint_index"] = 0
                        report["return_segments"] = [waypoint["segment"] for waypoint in state["return_waypoints"]]
                        begin_next_return_segment(game, position)
                    else:
                        report["success"] = True
                        finish()
            elif state.get("returning"):
                begin_next_return_segment(game, position)
            else:
                report["success"] = True
                finish()
            return

        if remaining < state["last_distance"] - 5:
            state.update(last_distance=remaining, last_progress=now)
        elif now - state["last_progress"] > 2.0:
            segment.update(blocked_location=vlist(position), blocked_remaining_cm=round(remaining, 1))
            try:
                segment["capsule_block_trace"] = capsule_block_trace(
                    game, player, position, state["goal"], state["capsule_half_height"]
                )
            except Exception as error:
                segment["capsule_block_trace_error"] = str(error)
            finish(f"Character made no movement progress during {state['phase']}")
            return
        if position.z < min(state["start"].z, state["goal"].z) - 160:
            segment["fall_location"] = vlist(position)
            finish(f"Character fell off the stair route during {state['phase']}")
            return
        toward_goal = unreal.Vector(
            state["goal"].x - position.x,
            state["goal"].y - position.y,
            0,
        )
        toward_goal_length = math.hypot(toward_goal.x, toward_goal.y)
        if toward_goal_length > 1.0:
            toward_goal = toward_goal / toward_goal_length
        input_scale = 0.35 if remaining < 125.0 else 1.0
        player.add_movement_input(toward_goal, input_scale, True)
    except Exception:
        finish(traceback.format_exc())
    finally:
        state["busy"] = False


handle = unreal.register_slate_post_tick_callback(tick)
report["startup_phase"] = "callback_registered"
write_live()
