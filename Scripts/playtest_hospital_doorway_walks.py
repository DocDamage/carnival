"""PIE: the real character opens each listed hospital door with context interact and walks straight through it
along the door's own axis, both directions (CARNIVAL_DOORS, default BP_Door_02a6,BP_Door_02a4). Records how far past
the frame it got and what stopped it. No saves."""
import json
import math
import os
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT = Path(r"F:\Carnival\Saved\WorldExpansion\HospitalDoorwayWalks_20261001.json")
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
DOORS = os.environ.get("CARNIVAL_DOORS", "BP_Door_02a6,BP_Door_02a4").split(",")
R = {"success": False, "errors": [], "walks": []}
S = {"phase": "wait", "busy": False, "deadline": time.monotonic() + 400, "jobs": [(d, s) for d in DOORS for s in (1, -1)]}


def leaf_yaws(door):
    return [round(c.get_editor_property("relative_rotation").yaw) for c in door.get_components_by_class(unreal.StaticMeshComponent)
            if c.static_mesh and ("Door_Plate" in c.static_mesh.get_name() or c.static_mesh.get_name() in ("SM_Door02_D", "SM_Door02_E"))]


def save():
    OUT.write_text(json.dumps(R, indent=1, default=str))


def finish(err=None):
    if err:
        R["errors"].append(err)
    R["success"] = not R["errors"] and all(w.get("crossed") for w in R["walks"])
    save()
    LE.editor_request_end_play()
    S.update(phase="exit", until=time.monotonic() + 5)


def tick(_):
    if S["busy"]:
        return
    S["busy"] = True
    try:
        now = time.monotonic()
        if S["phase"] == "exit":
            if now > S["until"]:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if now > S["deadline"]:
            raise RuntimeError("timeout in " + S["phase"])
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        p = unreal.GameplayStatics.get_player_pawn(game, 0)
        if not isinstance(p, unreal.CarnivalPlayerCharacter):
            return
        if S["phase"] == "wait":
            S.update(phase="next", until=now + 6)
            return
        if S["phase"] == "next":
            if now < S["until"]:
                return
            if not S["jobs"]:
                finish()
                return
            label, sg = S["jobs"].pop(0)
            d = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.Actor) if a.get_actor_label() == label)
            fr = [c for c in d.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh and "Frame" in c.static_mesh.get_name()]
            o = unreal.SystemLibrary.get_component_bounds(fr[0])[0] if fr else d.get_actor_location()
            f = d.get_actor_forward_vector(); f.z = 0; f = f.normal()
            st = o + f * (130 * sg); st.z = o.z - 20
            dirv = f * (-sg)
            p.get_movement_component().stop_movement_immediately()
            p.set_actor_location(st, False, True)
            p.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=math.degrees(math.atan2(dirv.y, dirv.x))), True)
            S.update(phase="open", until=now + 1.0, door=d, label=label, o=o, dirv=dirv, start=st, sg=sg)
            return
        if S["phase"] == "open":
            if now < S["until"]:
                return
            before = leaf_yaws(S["door"])
            target = p.find_nearby_door()
            # Press once per door, on the first approach (closed and ajar doors alike); the return walk uses the
            # door as the first walk left it.
            if S["label"] not in S.setdefault("pressed", set()):
                S["pressed"].add(S["label"])
                p.try_context_interact()
            S.update(phase="walk", until=now + 7, push=now + 0.8, interact={
                "locomotion": str(p.get_editor_property("locomotion_state")),
                "found_door": target.get_actor_label() if target else None, "leaf_yaw_before": before})
            return
        if S["phase"] == "walk":
            if now > S["push"]:
                p.add_movement_input(S["dirv"], 1.0, True)
            if now > S["until"]:
                o, dv = S["o"], S["dirv"]
                d0 = (S["start"] - o).dot(dv)
                d1 = (p.get_actor_location() - o).dot(dv)
                pos = p.get_actor_location()
                hit = unreal.SystemLibrary.capsule_trace_single(game, pos, pos + dv * 120, 42, 88,
                                                                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [p],
                                                                unreal.DrawDebugTrace.NONE, True)
                t = hit.to_tuple() if hit else None
                R["walks"].append({"door": S["label"], "from_side": S["sg"], "start_cm": round(d0), "end_cm": round(d1),
                                   "crossed": d1 > 150, "interact": S["interact"], "leaf_yaw_after_walk": leaf_yaws(S["door"]),
                                   "blocker_ahead": t[9].get_actor_label() if t and t[0] and t[9] else None})
                save()
                S.update(phase="next", until=now + 0.5)
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
