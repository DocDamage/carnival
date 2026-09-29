"""Walk between connected mansion room approaches with the real PIE character."""

import json
import math
import os
import time
import traceback
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
ROUTE_NAME = os.environ.get("CARNIVAL_TEST_ROOM_ROUTE", "foyer_to_study")
ROUTES = {
    "foyer92_to_foyer93": (
        [-70105.17, -86766.43, 915.1290498635826],
        [-70650.5, -86384.58, 915.1290498635826],
    ),
    "foyer93_to_study": (
        [-70650.5, -86384.58, 915.1290498635826],
        [-70233.2, -88562.48, 916.2216246281739],
    ),
    "foyer93_to_study_path": (
        [-70650.5, -86384.58, 915.1290498635826],
        [-70233.2, -88562.48, 916.2216246281739],
    ),
    "foyer92_to_study_full_path": (
        [-70105.17, -86766.43, 915.1290498635826],
        [-70233.2, -88562.48, 916.2216246281739],
    ),
    "study_to_foyer92_full_path": (
        [-70233.2, -88562.48, 916.2216246281739],
        [-70105.17, -86766.43, 915.1290498635826],
    ),
    "study_to_music_path": (
        [-70233.2, -88562.48, 916.2216246281739],
        [-71082.33, -88852.89, 913.7641318635826],
    ),
    "music_to_study_path": (
        [-71082.33, -88852.89, 913.7641318635826],
        [-70233.2, -88562.48, 916.2216246281739],
    ),
    "foyer_to_study": (
        [-70105.17, -86766.43, 915.1290498635826],
        [-70233.2, -88562.48, 916.2216246281739],
    ),
    "study_to_foyer": (
        [-70233.2, -88562.48, 916.2216246281739],
        [-70105.17, -86766.43, 915.1290498635826],
    ),
    "foyer_to_music": (
        [-70105.17, -86766.43, 915.1290498635826],
        [-71082.33, -88852.89, 913.7641318635826],
    ),
    "music_to_foyer": (
        [-71082.33, -88852.89, 913.7641318635826],
        [-70105.17, -86766.43, 915.1290498635826],
    ),
    "study_to_music": (
        [-70233.2, -88562.48, 916.2216246281739],
        [-71082.33, -88852.89, 913.7641318635826],
    ),
    "music_to_study": (
        [-71082.33, -88852.89, 913.7641318635826],
        [-70233.2, -88562.48, 916.2216246281739],
    ),
    "door7_gate_acceptance": (
        [-69868.95170657091, -88813.55549993354, 917.4216093693849],
        [-70075.43923100096, -89108.45025194412, 914.9641798635825],
    ),
}
if ROUTE_NAME not in ROUTES:
    raise ValueError(f"Unknown room route {ROUTE_NAME}; choose from {', '.join(ROUTES)}")

START_POINT, GOAL_POINT = ROUTES[ROUTE_NAME]
PATH_ROUTE_SEGMENTS = {
    "foyer93_to_study_path": "Foyer floor 93 to study",
    "foyer92_to_study_full_path": "Foyer floor 93 to study",
    "study_to_foyer92_full_path": "Foyer floor 93 to study",
    "study_to_music_path": "Study to music room table",
    "music_to_study_path": "Study to music room table",
}
ROOM_ROUTE_REPORT = ROOT / "Saved/MansionConnection/Mission_Room_Routes.json"
REPORT_PATH = ROOT / f"Saved/MansionConnection/RoomWalk_PIE_{ROUTE_NAME}.json"
LIVE_PATH = ROOT / f"Saved/MansionConnection/RoomWalk_PIE_{ROUTE_NAME}_Live.json"
report = {
    "map": MAP,
    "route": ROUTE_NAME,
    "start_approach": START_POINT,
    "goal_approach": GOAL_POINT,
    "saved_map_modified": False,
    "success": False,
    "samples": [],
}
state = {"phase": "setup", "deadline": time.monotonic() + 120, "busy": False, "polls": 0}


def write_live():
    LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"phase": state["phase"], "time": time.time(), "report": report}
    if state.get("player"):
        payload["player_position"] = list(state["player"].get_actor_location().to_tuple())
    LIVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


current_world = unreal.EditorLevelLibrary.get_editor_world()
if current_world and current_world.get_name() == "LV_Carnival":
    world = current_world
    report["reused_editor_startup_map"] = True
else:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    report["reused_editor_startup_map"] = False
if not world:
    raise RuntimeError(f"Could not load {MAP}")

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report["excluded_crowd_spawners"] = []
for actor in list(actor_subsystem.get_all_level_actors()):
    if actor.get_class().get_name() == "MetaHumanMassSpawner":
        report["excluded_crowd_spawners"].append(actor.get_actor_label())
        actor_subsystem.destroy_actor(actor)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.editor_request_begin_play()
state["deadline"] = time.monotonic() + 120
write_live()


def as_hit(value):
    return value.to_tuple() if value else None


def floor_trace(game, x, y, z, ignored=()):
    hit = as_hit(unreal.SystemLibrary.line_trace_single(
        game,
        unreal.Vector(x, y, z + 100.0),
        unreal.Vector(x, y, z - 1200.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        list(ignored),
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    if not hit or not hit[0]:
        return None
    return {"point": hit[5], "normal": hit[7], "actor": hit[9].get_actor_label() if hit[9] else None}


def block_trace(game, player, start, goal, half_height):
    hit = as_hit(unreal.SystemLibrary.capsule_trace_single(
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
    ))
    if not hit or not hit[0]:
        return {"blocked": False}
    return {
        "blocked": True,
        "actor": hit[9].get_actor_label() if hit[9] else None,
        "impact_point": list(hit[5].to_tuple()) if hit[5] else None,
        "impact_normal": list(hit[7].to_tuple()) if hit[7] else None,
    }


def finish(error=None):
    if error:
        report["error"] = error
    report["final_phase"] = state["phase"]
    for component, rotation in state.get("door7_original_rotations", []):
        try:
            component.set_relative_rotation(rotation, False, True)
        except Exception:
            pass
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_live()
    levels.editor_request_end_play()
    state.update(phase="exit", deadline=time.monotonic() + 2)


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
            return
        if state["phase"] == "setup":
            player = unreal.GameplayStatics.get_player_pawn(game, 0)
            if not player:
                state["polls"] += 1
                return
            capsule = player.get_component_by_class(unreal.CapsuleComponent)
            try:
                half_height = capsule.get_scaled_capsule_half_height() if capsule else 98.2
            except Exception:
                half_height = 98.2
            state.update(game=game, player=player, half_height=half_height)
            report["player_class"] = player.get_class().get_name()
            report["capsule_half_height_cm"] = half_height
            if ROUTE_NAME == "door7_gate_acceptance":
                runtime_actors = unreal.GameplayStatics.get_all_actors_of_class(game, unreal.Actor)
                door = next((actor for actor in runtime_actors if actor.get_actor_label() == "BP_Door7"), None)
                if not door:
                    finish("Could not find BP_Door7 in the PIE world")
                    return
                leaves = {
                    component.get_name(): component
                    for component in door.get_components_by_class(unreal.StaticMeshComponent)
                }
                left, right = leaves.get("SM_Door02_D"), leaves.get("SM_Door02_E")
                if not left or not right:
                    finish("BP_Door7 is missing one or both door leaf components in PIE")
                    return
                left_original = left.get_editor_property("relative_rotation")
                right_original = right.get_editor_property("relative_rotation")
                state["door7"] = {"left": left, "right": right}
                state["door7_original_rotations"] = [(left, left_original), (right, right_original)]
                report["door7"] = {
                    "actor": door.get_path_name(),
                    "left_leaf": left.get_name(),
                    "right_leaf": right.get_name(),
                    "starts_closed": True,
                }
            start_floor = floor_trace(game, *START_POINT)
            goal_floor = floor_trace(game, *GOAL_POINT)
            if not start_floor or not goal_floor:
                finish("No floor support at the room start or goal approach")
                return
            report["start_floor"] = {"actor": start_floor["actor"], "point": list(start_floor["point"].to_tuple())}
            report["goal_floor"] = {"actor": goal_floor["actor"], "point": list(goal_floor["point"].to_tuple())}
            start = start_floor["point"] + unreal.Vector(0.0, 0.0, half_height + 2.0)
            goal = goal_floor["point"] + unreal.Vector(0.0, 0.0, half_height)

            if ROUTE_NAME in PATH_ROUTE_SEGMENTS:
                room_routes = json.loads(ROOM_ROUTE_REPORT.read_text(encoding="utf-8"))
                route_segment_name = PATH_ROUTE_SEGMENTS[ROUTE_NAME]
                segment = next(item for item in room_routes["segments"] if item["name"] == route_segment_name)
                if not segment.get("success") or not segment.get("route", {}).get("path"):
                    finish(f"The static guide route is unavailable: {route_segment_name}")
                    return
                source_nodes = segment["route"]["path"]
                path_points = [unreal.Vector(*item["position"]) for item in source_nodes]
                if ROUTE_NAME in ("study_to_foyer92_full_path", "music_to_study_path"):
                    path_points.reverse()
                # Greedily retain the farthest static route point the actual PIE
                # capsule can reach in a single visibility-channel sweep.
                smoothed = [path_points[0]]
                index = 0
                while index < len(path_points) - 1:
                    selected = index + 1
                    for candidate in range(len(path_points) - 1, index, -1):
                        hit = as_hit(unreal.SystemLibrary.capsule_trace_single(
                            game,
                            path_points[index],
                            path_points[candidate],
                            42.0,
                            half_height,
                            unreal.TraceTypeQuery.ECC_VISIBILITY,
                            False,
                            [player],
                            unreal.DrawDebugTrace.NONE,
                            True,
                        ))
                        if not hit or not hit[0]:
                            selected = candidate
                            break
                    smoothed.append(path_points[selected])
                    index = selected
                if ROUTE_NAME == "foyer92_to_study_full_path":
                    smoothed = [start] + smoothed
                elif ROUTE_NAME == "study_to_foyer92_full_path":
                    smoothed.append(goal)
                report["static_guide"] = {
                    "report": str(ROOM_ROUTE_REPORT),
                    "segment": route_segment_name,
                    "source_node_count": len(path_points),
                    "PIE_capsule_waypoint_count": len(smoothed),
                    "capsule_clearance_used": True,
                }
                report["planned_waypoints"] = [list(point.to_tuple()) for point in smoothed]
                state["route_waypoints"] = smoothed
                state["route_waypoint_index"] = 1
                goal = smoothed[1] if len(smoothed) > 1 else smoothed[0]
                state["using_static_guide"] = True
            else:
                state["using_static_guide"] = False

            player.get_movement_component().stop_movement_immediately()
            player.set_actor_location(start, False, True)
            direction = unreal.Vector(goal.x - start.x, goal.y - start.y, 0.0)
            distance = math.hypot(direction.x, direction.y)
            if distance < 1.0:
                finish("Room start and goal approaches overlap")
                return
            direction = direction / distance
            player.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=math.degrees(math.atan2(direction.y, direction.x)), roll=0.0), True)
            state.update(
                phase="walk",
                start=start,
                goal=goal,
                last_distance=distance,
                last_progress=unreal.GameplayStatics.get_time_seconds(game),
                last_sample=-1.0,
                started=unreal.GameplayStatics.get_time_seconds(game),
            )
            report["setup"] = "PIE character positioned at sampled room approach"
            write_live()
            return

        player = state["player"]
        now = unreal.GameplayStatics.get_time_seconds(game)
        position = player.get_actor_location()
        goal = state["goal"]
        remaining = math.hypot(goal.x - position.x, goal.y - position.y)
        if now - state["last_sample"] >= 0.5:
            support = floor_trace(game, position.x, position.y, position.z, [player])
            report["samples"].append({
                "seconds": round(now - state["started"], 2),
                "position": list(position.to_tuple()),
                "horizontal_remaining_cm": round(remaining, 1),
                "floor_actor": support["actor"] if support else None,
                "floor_z": support["point"].z if support else None,
                "velocity": list(player.get_velocity().to_tuple()),
            })
            state["last_sample"] = now
            write_live()
        support = floor_trace(game, position.x, position.y, position.z, [player])
        if remaining < 80.0 and support and abs(position.z - support["point"].z - state["half_height"]) < 45.0:
            if state.get("using_static_guide"):
                state["route_waypoint_index"] += 1
                if state["route_waypoint_index"] < len(state["route_waypoints"]):
                    goal = state["route_waypoints"][state["route_waypoint_index"]]
                    goal_floor = floor_trace(game, goal.x, goal.y, goal.z, [player])
                    if not goal_floor:
                        finish(f"No floor support at static route waypoint {state['route_waypoint_index']}")
                        return
                    goal = goal_floor["point"] + unreal.Vector(0.0, 0.0, state["half_height"])
                    direction = unreal.Vector(goal.x - position.x, goal.y - position.y, 0.0)
                    distance = math.hypot(direction.x, direction.y)
                    direction = direction / max(distance, 1.0)
                    state.update(
                        goal=goal,
                        last_distance=distance,
                        last_progress=now,
                        last_sample=now - 1.0,
                    )
                    report["reached_guide_waypoint_count"] = state["route_waypoint_index"]
                    write_live()
                    return
            if ROUTE_NAME == "door7_gate_acceptance":
                report["open_gate_crossed"] = True
                report["open_gate_finish"] = list(position.to_tuple())
                report["success"] = bool(report.get("closed_gate_blocked_at_door"))
                if not report["success"]:
                    finish("The player crossed BP_Door7 without first being blocked by its closed leaves")
                    return
            else:
                report["success"] = True
            report["seconds"] = round(now - state["started"], 2)
            report["finish"] = list(position.to_tuple())
            finish()
            return
        if remaining < state["last_distance"] - 5.0:
            state.update(last_distance=remaining, last_progress=now)
        elif now - state["last_progress"] > 2.0:
            report["blocked_location"] = list(position.to_tuple())
            report["blocked_remaining_cm"] = round(remaining, 1)
            try:
                blocker = block_trace(game, player, position, goal, state["half_height"])
                report["capsule_block_trace"] = blocker
            except Exception as error:
                report["capsule_block_trace_error"] = str(error)
                blocker = None
            if ROUTE_NAME == "door7_gate_acceptance" and not state.get("door7_open"):
                if not blocker or blocker.get("actor") != "BP_Door7":
                    finish("Closed-door attempt stopped before confirming BP_Door7 as the blocker")
                    return
                report["closed_gate_blocked_at_door"] = {
                    "actor": blocker.get("actor"),
                    "impact_point": blocker.get("impact_point"),
                    "player_location": list(position.to_tuple()),
                    "remaining_cm": round(remaining, 1),
                }
                left = state["door7"]["left"]
                right = state["door7"]["right"]
                left_original = state["door7_original_rotations"][0][1]
                right_original = state["door7_original_rotations"][1][1]
                left.set_relative_rotation(unreal.Rotator(
                    pitch=left_original.pitch, yaw=left_original.yaw + 90.0, roll=left_original.roll
                ), False, True)
                right.set_relative_rotation(unreal.Rotator(
                    pitch=right_original.pitch, yaw=right_original.yaw - 90.0, roll=right_original.roll
                ), False, True)
                state["door7_open"] = True
                report["door7"]["opened_transiently_after_block"] = True
                state.update(last_distance=remaining, last_progress=now, last_sample=now - 1.0)
                write_live()
                return
            finish("Character made no movement progress")
            return
        direction = unreal.Vector(goal.x - position.x, goal.y - position.y, 0.0)
        direction_length = math.hypot(direction.x, direction.y)
        if direction_length > 1.0:
            direction = direction / direction_length
            player.add_movement_input(direction, 0.35 if remaining < 125.0 else 1.0, True)
    except Exception:
        finish(traceback.format_exc())
    finally:
        state["busy"] = False


handle = unreal.register_slate_post_tick_callback(tick)
write_live()
