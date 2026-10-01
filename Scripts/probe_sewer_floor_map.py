"""Read-only: top-down text map of the Sewers at 1 m resolution, to see where the unreachable Cube4 floor
(z -1850) sits relative to the walked corridor. Per column (x -29500..-23000, y -20000..-9000) the first floor hit
between z -1300 and -2100 is classified, then a standing capsule at that floor tells open space from wall:
  W walkway/other floor above -1830   c Cube4 floor   x other floor at or below -1830
  # standing capsule blocked (wall/prop)   . no floor   S the reachable audit entrance."""
import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\Reachability\sewer_floor_map_20261001")
OUT.mkdir(parents=True, exist_ok=True)
V = unreal.Vector
TQ = unreal.TraceTypeQuery.ECC_VISIBILITY
N = unreal.DrawDebugTrace.NONE
X0, X1, Y0, Y1, STEP = -29500, -23000, -20000, -9000, 100
ENTRANCE = (-27050, -11100)
R = {"success": False, "errors": [], "legend": __doc__, "counts": {}}
try:
    w = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    rows = []
    counts = {}
    floors = {}
    for y in range(Y1, Y0 - 1, -STEP):  # north (larger y) at the top
        row = []
        for x in range(X0, X1 + 1, STEP):
            if abs(x - ENTRANCE[0]) < STEP / 2 + 1 and abs(y - ENTRANCE[1]) < STEP / 2 + 1:
                row.append("S"); continue
            h = unreal.SystemLibrary.line_trace_single(w, V(x, y, -1300), V(x, y, -2100), TQ, False, [], N, True)
            t = h.to_tuple() if h else None
            if not (t and t[0]):
                ch = "."
            else:
                z = t[4].z
                name = t[9].get_actor_label() if t[9] else "?"
                blocked = unreal.SystemLibrary.capsule_trace_single(w, V(x, y, z + 100), V(x, y, z + 100.5), 40, 85, TQ, False, [], N, True)
                bt = blocked.to_tuple() if blocked else None
                if bt and bt[0]:
                    ch = "#"
                elif name == "Cube4":
                    ch = "c"
                elif z > -1830:
                    ch = "W"
                else:
                    ch = "x"
                if ch in "cWx":
                    floors[name] = floors.get(name, 0) + 1
            counts[ch] = counts.get(ch, 0) + 1
            row.append(ch)
        rows.append("".join(row))
    (OUT / "map.txt").write_text("\n".join(rows))
    R["counts"] = counts
    R["floors"] = dict(sorted(floors.items(), key=lambda kv: -kv[1])[:20])
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
(OUT / "index.json").write_text(json.dumps(R, indent=1))
print("SEWER_MAP_DONE")
