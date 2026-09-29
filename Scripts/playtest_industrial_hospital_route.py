"""Exercise the saved hospital road in PIE with real pawn movement and collision.

API-driven controls are not a physical-controller or visual acceptance test.
Only the initial position of each independent travel mode is teleported. Both
directions within a mode must be traversed continuously at normal game speed.
The crowd spawner is excluded in the unsaved test world, never in saved maps.
"""
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
import unreal

sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import MAIN_MAP, OUT, world_point

layout = json.loads((OUT / "Industrial_Hospital_Route_Meshes.json").read_text())
# The rendered road has a 14 cm crown above these source spline samples.
forward = [unreal.Vector(*world_point(p)) + unreal.Vector(0, 0, 14)
           for p in layout["route_points_local_cm"]]
start_index = globals().get("ROUTE_START_INDEX", 0)
end_index = globals().get('ROUTE_END_INDEX')
forward = forward[start_index:end_index]
if globals().get("WORLD_ROUTE_POINTS"):
    forward = [unreal.Vector(*point) for point in globals()["WORLD_ROUTE_POINTS"]]
report_prefix = globals().get("REPORT_PREFIX", "Route_Playtest")
report_prefix = os.environ.get("CARNIVAL_ROUTE_REPORT_PREFIX", report_prefix)
walk_only = os.environ.get("CARNIVAL_WALK_ONLY") == "1" or globals().get("WALK_ONLY", False)
time_dilation = float(os.environ.get("CARNIVAL_ROUTE_TIME_DILATION", "1.0"))
report = {"success": False, "map": MAIN_MAP, "tests": [], "errors": [],
          "route_start_index": start_index, 'route_end_index':end_index,
          "time_dilation": time_dilation, "input_method": "pawn movement and motorcycle input APIs",
          "excluded_unrelated_crowd_spawners": [],
          "route_length_m": sum(math.dist(a.to_tuple(), b.to_tuple()) for a,b in zip(forward,forward[1:]))/100}
state = {"phase": "setup", "busy": False, "deadline": time.monotonic() + 180}
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
if not world:
    raise RuntimeError("Could not load the connected Carnival map")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(eas.get_all_level_actors()):
    if actor.get_class().get_name() == "MetaHumanMassSpawner":
        report["excluded_unrelated_crowd_spawners"].append(actor.get_actor_label())
        eas.destroy_actor(actor)

def write_report():
    (OUT / (report_prefix + ".json")).write_text(json.dumps(report, indent=2), encoding="utf-8")

def xy(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def reached_waypoint(pos, route, index):
    if xy(pos, route[index]) < 180:
        return True
    if state["mode"] != "motorcycle" or index == 0:
        return False
    # A vehicle may pass beside a sample during a turn. Accept crossing its
    # perpendicular plane only within the 9 m lane and a short local segment.
    tangent = route[index] - route[index-1]
    length = max(1, math.hypot(tangent.x, tangent.y))
    dx, dy = pos.x-route[index].x, pos.y-route[index].y
    along = (dx*tangent.x+dy*tangent.y)/length
    across = abs(dx*tangent.y-dy*tangent.x)/length
    return 0 <= along < 500 and across < 350

def finish(error=None):
    if error:
        report["errors"].append(error)
    report["phase"] = state["phase"]
    report["last_index"] = state.get("index")
    for actor in (state.get("bike"),):
        if actor:
            actor.input_throttle(0)
            actor.input_steering(0)
            actor.input_brake(1)
    write_report()
    levels.editor_request_end_play()
    state.update(phase="exit", deadline=time.monotonic() + 3)

def begin_leg(mode, reverse=False):
    route = list(reversed(forward)) if reverse else forward
    actor = state["player"] if mode == "walk" else state["bike"]
    player = state["player"]
    if not reverse:
        d = route[1] - route[0]
        yaw = math.degrees(math.atan2(d.y, d.x))
        player.get_movement_component().stop_movement_immediately()
        if mode == "walk":
            actor.set_actor_location(route[0] + unreal.Vector(0, 0, 105), False, True)
            actor.set_actor_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0), True)
        else:
            actor.input_throttle(0)
            actor.input_brake(1)
            bike_location = route[0] + unreal.Vector(0, 0, 4)
            actor.set_actor_location(bike_location, False, True)
            actor.set_actor_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0), True)
            right = unreal.Vector(-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0)
            approach = bike_location - right * 60 + unreal.Vector(0, 0, 98.195294)
            player.set_actor_location(approach, False, True)
            actor.mount(player, True)
            actor.input_brake(0)
    now = unreal.GameplayStatics.get_time_seconds(state["game"])
    name = mode + ("_return" if reverse else "_outbound")
    state.update(phase=name, mode=mode, reverse=reverse, route=route, actor=actor,
                 index=1, last_index=0, last_progress=now, start=now, next_sample=now,
                 deadline=time.monotonic() + 1200)
    report["tests"].append({"name": name, "success": False, "samples": [],
                             "start": actor.get_actor_location().to_tuple()})
    write_report()

def tick(delta):
    if state["busy"]:
        return
    state["busy"] = True
    try:
        if state["phase"] == "exit":
            if time.monotonic() >= state["deadline"]:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if time.monotonic() > state["deadline"]:
            finish("Wall-clock timeout in " + state["phase"])
            return
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        if state["phase"] == "setup":
            player = unreal.GameplayStatics.get_player_pawn(game, 0)
            bikes = list(unreal.GameplayStatics.get_all_actors_of_class(game, unreal.CarnivalMotorcycle))
            if not player or not bikes:
                return
            if not isinstance(player, unreal.CarnivalPlayerCharacter):
                raise RuntimeError("Unexpected player pawn: " + player.get_class().get_name())
            state.update(game=game, player=player, bike=bikes[0])
            report.update(player_class=player.get_class().get_name(), motorcycle_class=bikes[0].get_class().get_name())
            unreal.GameplayStatics.set_global_time_dilation(game, time_dilation)
            begin_leg(globals().get("START_MODE", "walk"))
            return
        actor, route = state["actor"], state["route"]
        pos = actor.get_actor_location()
        now = unreal.GameplayStatics.get_time_seconds(game)
        # Advance through nearby consecutive samples only; never skip a stretch
        # of road because a later curve happens to be spatially close.
        while state["index"] < len(route) - 1 and reached_waypoint(pos, route, state["index"]):
            state["index"] += 1
        if state["index"] > state["last_index"]:
            state.update(last_index=state["index"], last_progress=now)
        if now - state["last_progress"] > 25:
            report["stuck_location"] = pos.to_tuple()
            finish("No waypoint progress for 25 game seconds")
            return
        if pos.z < route[state["index"]].z - 180:
            report["fall_location"] = pos.to_tuple()
            finish("Pawn fell below the authored road")
            return
        current = report["tests"][-1]
        if now >= state["next_sample"]:
            sample = {"index": state["index"], "position": pos.to_tuple(), "seconds": round(now-state["start"], 2)}
            if state['mode']=='motorcycle':
                hit=actor.get_editor_property('last_movement_hit').to_tuple()
                sample.update(speed=actor.current_speed,rotation=actor.get_actor_rotation().to_tuple(),
                    collision={'blocked':bool(hit[0]),'initial_overlap':bool(hit[1]),
                               'actor':hit[9].get_name() if hit[9] else None,
                               'point':hit[5].to_tuple(),'normal':hit[7].to_tuple()})
            current["samples"].append(sample)
            (OUT / (report_prefix + "_Live.json")).write_text(json.dumps({"mode": state["phase"], "total": len(route), **sample}))
            state["next_sample"] = now + 5
            write_report()
        if state["index"] == len(route) - 1 and xy(pos, route[-1]) < 150:
            current.update(success=True, seconds=round(now-state["start"], 2), finish=pos.to_tuple())
            if not state["reverse"]:
                begin_leg(state["mode"], True)
            elif state["mode"] == "walk" and not walk_only:
                begin_leg("motorcycle")
            else:
                report["success"] = True
                finish()
            return
        target_index = state["index"]
        lookahead = 170 if state["mode"] == "walk" else 500
        while target_index < len(route) - 1 and xy(pos, route[target_index]) < lookahead:
            target_index += 1
        d = route[target_index] - pos
        direction = unreal.Vector(d.x, d.y, 0) / max(1, math.hypot(d.x, d.y))
        if state["mode"] == "walk":
            actor.add_movement_input(direction, 1.0, True)
        else:
            desired = math.degrees(math.atan2(d.y, d.x))
            error = (desired - actor.get_actor_rotation().yaw + 180) % 360 - 180
            actor.input_steering(max(-1, min(1, error / 13)))
            # Slow before the endpoint and during a tight turn, just as a rider
            # would. Normal traversal throttle cannot turn inside the forecourt.
            tight_turn = abs(error) > 35 or xy(pos, route[-1]) < 2000
            actor.input_throttle(.05 if tight_turn else (.29 if abs(error) < 15 else .18))
    except Exception:
        finish(traceback.format_exc())
    finally:
        state["busy"] = False

write_report()
levels.editor_request_begin_play()
handle = unreal.register_slate_post_tick_callback(tick)
