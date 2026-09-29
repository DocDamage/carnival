"""Apply the probed street alignment and keep the scanned facade beside the road."""
import bisect
import json
import runpy
import shutil
import sys
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import OUT, ROUTE_LEVEL, HOSPITAL_EXTERIOR_LEVEL, FACADE_LOCAL

layout = json.loads((OUT / "Industrial_Hospital_Route_Meshes.json").read_text())
runpy.run_path(str(ROOT / "Scripts/reimport_industrial_route_geometry.py"), init_globals={
    "MESH_NAMES": [m["name"] for m in layout["road_meshes"]],
})
points = layout["route_points_local_cm"]
stations = [p[0] for p in points]

def point_on_route(s):
    i = min(len(points)-2, max(0, bisect.bisect_right(stations, s)-1))
    a, b = points[i:i+2]
    t = min(1, max(0, (s-a[0])/(b[0]-a[0])))
    return tuple(a[k]*(1-t)+b[k]*t for k in range(3))

report = {"success": False, "backups": [], "changes": []}
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for path in (ROUTE_LEVEL, HOSPITAL_EXTERIOR_LEVEL):
    file = ROOT / "Content" / (path.removeprefix("/Game/") + ".umap")
    backup = OUT / "Backups" / (file.stem + "_before_clearance_" + stamp + ".umap")
    shutil.copy2(file, backup)
    report["backups"].append(str(backup))
    world = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not world:
        raise RuntimeError("Could not load " + path)
    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    targets = {}
    if path == ROUTE_LEVEL:
        for i, s in enumerate((67000, 71000, 99000, 141000), 1):
            x, y, z = point_on_route(s)
            targets[f"Slum Road Sodium Light {i:02d}"] = (x, y + (-680 if i % 2 else 680), z + 430)
        for name, s in (("Abandoned Toy Assembly Line", 66000), ("Night Shift at Toy Factory", 102000), ("Malfunctioning Animatronics", 145000)):
            x, y, z = point_on_route(s)
            targets[name] = (x, y+550, z+80)
        for i, s in enumerate((38000, 69000, 97000, 122000, 143000), 1):
            x, y, z = point_on_route(s)
            targets[f"Hospital Approach Fog {i:02d}"] = (x, y, z+1100)
    else:
        x, y, z = FACADE_LOCAL
        targets = {"Abandoned Hospital Factory-Gate Facade": FACADE_LOCAL,
                   "Gate Sodium Lamp West": (x-3500, y+800, z+1200),
                   "Gate Sodium Lamp East": (x+3500, y+800, z+1200)}
    for label, position in targets.items():
        if label not in actors:
            raise RuntimeError("Expected authored actor is missing: " + label)
        actor = actors[label]
        before = actor.get_actor_location().to_tuple()
        actor.modify()
        actor.set_actor_location(unreal.Vector(*position), False, True)
        report["changes"].append({"level": path, "label": label, "before": before, "after": position})
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, path):
        raise RuntimeError("Could not save " + path)
report["success"] = True
(OUT / "Route_Clearance_Correction.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
runpy.run_path(str(ROOT / "Scripts/audit_industrial_hospital_clearance.py"))
