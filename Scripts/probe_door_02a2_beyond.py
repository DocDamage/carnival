"""Read-only: what lies past a hospital door (CARNIVAL_DOOR, default BP_Door_02a2). Lists every blocking hit along the door's
passage axis (both directions, three heights, three lateral offsets) out to 10 m, the bounds and level of the
wall pieces behind it, and floor hits beyond them, so we can tell a real room from a fake door."""
import json
import os
import traceback
from pathlib import Path
import unreal

DOOR = os.environ.get("CARNIVAL_DOOR", "BP_Door_02a2")
OUT = Path(r"F:\Carnival\Saved\WorldExpansion") / ("Door02a2_Beyond_20261001.json" if DOOR == "BP_Door_02a2" else DOOR + "_Beyond_20261001.json")
V = unreal.Vector
R = {"success": False, "errors": []}
try:
    w = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    door = next(a for a in actors if a.get_actor_label() == DOOR)
    o, e = door.get_actor_bounds(False)
    f = door.get_actor_forward_vector(); f.z = 0; f = f.normal()
    r = door.get_actor_right_vector(); r.z = 0; r = r.normal()
    if os.environ.get("CARNIVAL_DOOR_AXIS") == "right":  # mansion BP_Door02: the passage runs along the actor's right
        f, r = r, f
    R["door"] = {"origin": o.to_tuple(), "forward": f.to_tuple(), "level": door.get_level().get_outermost().get_name()}
    floor_z = o.z - e.z
    rays = []
    for sign in (1, -1):
        for off in (-60, 0, 60):
            for h in (40, 100, 160):
                s = o + r * off; s.z = floor_z + h
                hits = unreal.SystemLibrary.line_trace_multi(w, s, s + f * (1000 * sign), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                            False, [door], unreal.DrawDebugTrace.NONE, True) or []
                rows = []
                for hit in hits:
                    t = hit.to_tuple(); a = t[9]
                    rows.append({"actor": a.get_actor_label() if a else "?", "dist": round(t[3]),
                                 "blocking": bool(t[0])})
                # also trace on Pawn channel style via sweep to catch non-visibility blockers
                cap = unreal.SystemLibrary.capsule_trace_multi(w, s, s + f * (1000 * sign), 35, 40,
                                                               unreal.TraceTypeQuery.TRACE_TYPE_QUERY2, False, [door],
                                                               unreal.DrawDebugTrace.NONE, True) or []
                crow = [{"actor": (c.to_tuple()[9].get_actor_label() if c.to_tuple()[9] else "?"),
                         "dist": round(c.to_tuple()[3])} for c in cap]
                rays.append({"dir": sign, "off": off, "h": h, "visibility": rows[:5], "camera_capsule": crow[:5]})
    R["rays"] = rays
    names = {h["actor"] for ray in rays for h in ray["visibility"][:1] + ray["camera_capsule"][:2] if h["dist"] < 150}
    R["walls"] = []
    for a in actors:
        if a.get_actor_label() in names:
            ao, ae = a.get_actor_bounds(False)
            if (ao - o).length() < 800:
                R["walls"].append({"label": a.get_actor_label(), "level": a.get_level().get_outermost().get_name().rsplit("/", 1)[1],
                                   "center": [round(v) for v in ao.to_tuple()], "extent": [round(v) for v in ae.to_tuple()],
                                   "yaw": round(a.get_actor_rotation().yaw, 1)})
    R["floor_beyond"] = []
    for d in (150, 300, 500, 800):
        for sign in (1, -1):
            p = o + f * (d * sign)
            hit = unreal.SystemLibrary.line_trace_single(w, V(p.x, p.y, floor_z + 250), V(p.x, p.y, floor_z - 400),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [door],
                                                         unreal.DrawDebugTrace.NONE, True)
            hit = hit.to_tuple() if hit else (False,) * 10
            R["floor_beyond"].append({"dir": sign, "dist": d, "hit": bool(hit[0]),
                                      "z": round(hit[4].z) if hit[0] else None,
                                      "actor": hit[9].get_actor_label() if hit[0] and hit[9] else None})
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
OUT.write_text(json.dumps(R, indent=1))
print("DOOR02A2_DONE")
