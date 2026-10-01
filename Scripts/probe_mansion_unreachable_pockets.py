"""Read-only: what encloses each unreachable pocket (CARNIVAL_POCKETS json, default the mansion audit
(Reachability/mansion_v5_doorsopen_20261001). For each pocket centroid: the first blocking hit of a standing
capsule swept 15 m in eight directions, the floor under it, and every BP_Door within 10 m with its tags."""
import json
import os
import math
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Reachability" / os.environ.get("CARNIVAL_POCKETS_OUT", "mansion_pockets_20261001.json")
POCKETS = json.loads(os.environ["CARNIVAL_POCKETS"]) if os.environ.get("CARNIVAL_POCKETS") else {
    "east_grounds": (-68888, -87879, 648),
    "top_floor_room": (-70527, -86610, 1920),
    "entrance_balcony": (-70095, -86127, 1380),
    "west_stair_landing": (-72789, -85674, 1332),
    "ground_floor_patch": (-69983, -87207, 818),
}
V = unreal.Vector
TQ = unreal.TraceTypeQuery.ECC_VISIBILITY
N = unreal.DrawDebugTrace.NONE
R = {"success": False, "errors": [], "pockets": {}}
try:
    w = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    doors = [a for a in acts if a.get_actor_label().startswith("BP_Door")]
    rides = [a for a in acts if "Ride" in a.get_class().get_name() or "Carnival" in a.get_class().get_name() and a.get_class().get_name().startswith("BP_")]
    for name, c in POCKETS.items():
        floor = unreal.SystemLibrary.line_trace_single(w, V(c[0], c[1], c[2] + 150), V(c[0], c[1], c[2] - 300), TQ, False, doors, N, True)
        ft = floor.to_tuple() if floor else None
        fz = ft[4].z if ft and ft[0] else c[2]
        rec = {"floor": (ft[9].get_actor_label() if ft and ft[0] and ft[9] else None), "floor_z": round(fz), "rays": [], "doors": []}
        start = V(c[0], c[1], fz + 95)
        for k in range(8):
            a = math.radians(k * 45)
            end = start + V(math.cos(a), math.sin(a), 0) * 1500
            h = unreal.SystemLibrary.capsule_trace_single(w, start, end, 40, 85, TQ, False, doors, N, True)
            t = h.to_tuple() if h else None
            rec["rays"].append({"yaw": k * 45, "hit": t[9].get_actor_label() if t and t[0] and t[9] else None,
                                "dist": round(t[3]) if t and t[0] else None, "start_blocked": bool(t and t[0] and t[3] < 1)})
        for d in doors:
            dist = (d.get_actor_location() - V(*c)).length()
            if dist < 1000:
                rec["doors"].append({"door": d.get_actor_label(), "dist": round(dist), "z": round(d.get_actor_location().z),
                                     "tags": [str(x) for x in d.get_editor_property("tags")]})
        rec["nearest_rides"] = sorted(({"actor": a.get_actor_label(), "dist": round((a.get_actor_location() - V(*c)).length())}
                                        for a in rides), key=lambda x: x["dist"])[:3]
        R["pockets"][name] = rec
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
OUT.write_text(json.dumps(R, indent=1))
print("MANSION_POCKETS_DONE")
