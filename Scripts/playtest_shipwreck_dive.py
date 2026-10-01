"""PIE: the real player swims R12 both ways. Start on the Atlantis hall floor beside the shaft, dive down the shaft
past the main deck, round the hull to the shipwreck_manifest station on the seabed, then swim back up into the hall.
Steering uses add_movement_input plus the character's swim-up / dive hold, like a player would. No saves."""
import json
import math
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/ShipwreckDeep_20261001"
REPORT = OUT / "dive_playtest.json"
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
HALL_START = (-7700.0, -10400.0, -1650.0)  # Atlantis floor (Portal_Part0, top -1750) at the shaft's west edge
DOWN = [(-6400.0, -10400.0, -2400.0),       # into the shaft
        (-6400.0, -10400.0, -3300.0),       # just above the main deck
        (-6100.0, -11600.0, -3300.0),       # over the south rail, clear of the hull side
        None]                               # the station, resolved at runtime
UP = [(-6100.0, -11600.0, -3300.0), (-6400.0, -10400.0, -3300.0), (-6400.0, -10400.0, -2400.0),
      (-7700.0, -10400.0, -1600.0)]
REACH = 220.0
R = {"success": False, "errors": [], "legs": []}
S = {"phase": "wait", "busy": False, "deadline": time.monotonic() + 400}


def save():
    REPORT.write_text(json.dumps(R, indent=1, default=str))


def finish(err=None):
    if err:
        R["errors"].append(err)
    R["success"] = not R["errors"] and len(R["legs"]) == 2 and all(l["success"] for l in R["legs"])
    save()
    LE.editor_request_end_play()
    S.update(phase="exit", deadline=time.monotonic() + 5)


def start_leg(name, points):
    leg = {"name": name, "success": False, "points": points, "samples": [], "max_depth_z": None}
    R["legs"].append(leg)
    S.update(phase="leg", leg=leg, points=[V(*p) for p in points], i=0,
             started=unreal.GameplayStatics.get_time_seconds(S["game"]), last_sample=-10.0)


def tick(_):
    if S["busy"]:
        return
    S["busy"] = True
    try:
        now = time.monotonic()
        if S["phase"] == "exit":
            if now > S["deadline"]:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if now > S["deadline"]:
            raise RuntimeError("wall-clock timeout in " + S["phase"])
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        p = unreal.GameplayStatics.get_player_pawn(game, 0)
        if not isinstance(p, unreal.CarnivalPlayerCharacter):
            return
        if S["phase"] == "wait":
            station = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.Actor)
                           if a.get_actor_label() == "Campaign_shipwreck_manifest")
            o, e = station.get_actor_bounds(False)
            R["station_bounds"] = {"center": o.to_tuple(), "extent": e.to_tuple()}
            DOWN[-1] = (o.x, o.y, o.z)
            S["game"] = game
            ctrl = p.get_controller()
            if ctrl:
                ctrl.set_ignore_move_input(False)
            unreal.SystemLibrary.execute_console_command(game, "t.IdleWhenNotForeground 0")
            p.get_movement_component().stop_movement_immediately()
            assert p.set_actor_location(V(*HALL_START), False, True), "teleport to Atlantis hall failed"
            S.update(phase="settle", until=now + 3)
            return
        if S["phase"] == "settle":
            if now >= S["until"]:
                start_leg("hall_to_station", DOWN)
            return
        # Leg steering.
        leg, pts = S["leg"], S["points"]
        pos = p.get_actor_location()
        gt = unreal.GameplayStatics.get_time_seconds(game)
        mv = p.get_movement_component()
        if leg["max_depth_z"] is None or pos.z < leg["max_depth_z"]:
            leg["max_depth_z"] = round(pos.z)
        target = pts[S["i"]]
        d = target - pos
        if d.length() < REACH:
            S["i"] += 1
            if S["i"] >= len(pts):
                leg.update(success=True, seconds=round(gt - S["started"], 1), finish_cm=pos.to_tuple(),
                           in_water=p.is_in_water_volume(), submerged=p.is_submerged())
                p.set_swim_up_held(False)
                p.set_swim_down_held(False)
                save()
                if leg["name"] == "hall_to_station":
                    start_leg("station_to_hall", UP)
                else:
                    finish()
                return
            target = pts[S["i"]]
            d = target - pos
        p.set_swim_down_held(d.z < -60)
        p.set_swim_up_held(d.z > 60)
        horiz = math.hypot(d.x, d.y)
        if horiz > 40:
            p.add_movement_input(V(d.x / horiz, d.y / horiz, 0), 1.0, True)
        if gt - S["last_sample"] >= 2.0:
            leg["samples"].append({"t": round(gt - S["started"], 1), "pos": [round(v) for v in pos.to_tuple()],
                                   "waypoint": S["i"], "mode": str(mv.movement_mode), "in_water": p.is_in_water_volume(),
                                   "submerged": p.is_submerged(), "seabed": p.is_seabed_walking()})
            S["last_sample"] = gt
            save()
        if gt - S["started"] > 150:
            leg["failure_cm"] = pos.to_tuple()
            leg["failed_waypoint"] = S["i"]
            finish(leg["name"] + ": did not reach waypoint %d within 150 s" % S["i"])
    except Exception:
        finish(traceback.format_exc())
    finally:
        S["busy"] = False


try:
    assert unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    for actor in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
        if actor.get_class().get_name() == "MetaHumanMassSpawner":
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
    save()
    handle = unreal.register_slate_post_tick_callback(tick)
    LE.editor_request_begin_play()
except Exception:
    R["errors"].append(traceback.format_exc())
    save()
    unreal.SystemLibrary.quit_editor()
