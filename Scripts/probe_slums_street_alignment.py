"""Evaluate lateral street alignments with standing-capsule collision sweeps."""
import json
import math
import runpy
import sys
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import MAIN_MAP, OUT, world_point
runpy.run_path(str(ROOT / "Scripts/reimport_industrial_route_geometry.py"))
world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
if not world:
    raise RuntimeError("Could not load connected world")
field = json.loads((OUT / "Source/Slum_Terrain_Heightfield.json").read_text())
xs, ys, heights = field["xs"], field["ys"], field["heights"]
nx = len(xs)

def ground(x, y):
    fx = min(nx-1.001, max(0, (x-xs[0])/200))
    fy = min(len(ys)-1.001, max(0, (y-ys[0])/200))
    ix, iy = int(fx), int(fy)
    tx, ty = fx-ix, fy-iy
    return sum(heights[(iy+j)*nx+ix+i] * (tx if i else 1-tx) * (ty if j else 1-ty)
               for j in (0, 1) for i in (0, 1))

results = []
for offset in (2500, 2800, 3000, 3200, 3500, 4000, 6000, 6500):
    rows = []
    for s in range(60000, 76001, 150):
        # Ease away from the old street before its first blocked house.
        alpha = min(1, (s-60000)/3500)
        lateral = offset * alpha*alpha*(3-2*alpha)
        # Grade above the sampled terrain across the full nine-metre lane.
        z = max(ground(-12000-lateral+side, s-60000) for side in (-450, 0, 450)) + 30
        rows.append((s, lateral, z))
    # A broad embankment removes short terrain steps without cutting through
    # existing scenery. The actual rebuilt spline will be audited separately.
    rows = [(s, side, max(p[2] - abs(p[0]-s)*.12 for p in rows)) for s, side, z in rows]
    blocked = []
    for lane in (-400, 0, 400):
        points = [unreal.Vector(*world_point((s, lateral+lane, z))) + unreal.Vector(0,0,99)
                  for s, lateral, z in rows]
        for i, (a,b) in enumerate(zip(points, points[1:])):
            hit = unreal.SystemLibrary.capsule_trace_single(world, a, b, 42, 96,
                unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True)
            h = hit.to_tuple() if hit else None
            if h and h[0] and not (h[7].z > .707 and h[5].z < max(a.z,b.z)-60):
                blocked.append({"s": rows[i][0], "lane": lane,
                    "actor": h[9].get_actor_label() if h[9] else None,
                    "point": h[5].to_tuple(), "normal": h[7].to_tuple()})
    results.append({"offset": offset, "blocked": blocked, "route_rows": rows})
(OUT / "Slums_Alignment_Probe.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
unreal.log("SLUMS_ALIGNMENT " + str([(r["offset"], len(r["blocked"])) for r in results]))
