"""Read-only: why the mansion's east grounds (audit cluster with SM_OuterStairs10, SM_ExternalFloor37/38 and
Landscape2) are unreachable. Reports those pieces' bounds, then sweeps a standing capsule from each toward the
front entrance and the reachable porch and lists every hit with its collision profile."""
import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\Reachability\mansion_east_grounds_20261001.json")
V = unreal.Vector
TQ = unreal.TraceTypeQuery.ECC_VISIBILITY
N = unreal.DrawDebugTrace.NONE
TARGETS = {"entrance": V(-70105, -86766, 820), "porch_ground": V(-70400, -85600, 650)}
R = {"success": False, "errors": [], "pieces": [], "sweeps": []}
try:
    w = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    doors = [a for a in acts if a.get_actor_label().startswith("BP_Door")]
    pieces = [a for a in acts if a.get_actor_label() in ("SM_OuterStairs10", "SM_ExternalFloor37", "SM_ExternalFloor38")]
    for p in pieces:
        o, e = p.get_actor_bounds(False)
        R["pieces"].append({"label": p.get_actor_label(), "center": [round(v) for v in o.to_tuple()], "extent": [round(v) for v in e.to_tuple()]})
        start = V(o.x, o.y, o.z + e.z + 100)
        for name, tgt in TARGETS.items():
            end = V(tgt.x, tgt.y, start.z)
            hits = unreal.SystemLibrary.capsule_trace_multi(w, start, end, 40, 85, TQ, False, doors, N, True) or []
            rows = []
            for h in hits[:6]:
                t = h.to_tuple(); a = t[9]; comp = t[10] if len(t) > 10 else None
                prof = None
                try:
                    prof = str(comp.get_collision_profile_name()) if comp else None
                except Exception:
                    pass
                rows.append({"actor": a.get_actor_label() if a else "?", "dist": round(t[3]), "z": round(t[4].z), "profile": prof,
                             "hidden": bool(a.is_hidden_ed()) if a else None})
            R["sweeps"].append({"from": p.get_actor_label(), "to": name, "hits": rows})
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
OUT.write_text(json.dumps(R, indent=1))
print("EAST_GROUNDS_DONE")
