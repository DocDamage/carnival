"""Read-only road capsule/floor audit and slum duplicate-geometry inventory."""
import json
import math
import sys
import traceback
from collections import defaultdict
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
sys.path.insert(0, str(ROOT / "Scripts"))
from industrial_hospital_route_config import MAIN_MAP, OUT, world_point

report = {"success": False, "errors": [], "samples": [], "missing_floor": [],
          "height_mismatches": [], "obstructions": [], "duplicate_mesh_transforms": []}

def hit_record(hit):
    h = hit.to_tuple() if hit else None
    if not h or not h[0]:
        return None
    actor = h[9]
    return {"actor": actor.get_actor_label() if actor else None,
            "actor_path": actor.get_path_name() if actor else None,
            "point": h[5].to_tuple(), "normal": h[7].to_tuple()}

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    if not world:
        raise RuntimeError("Connected world failed to load")
    route = json.loads((OUT / "Industrial_Hospital_Route_Meshes.json").read_text())
    points = [unreal.Vector(*world_point(p)) + unreal.Vector(0, 0, 14)
              for p in route["route_points_local_cm"]]
    centers = []
    for index, point in enumerate(points):
        h = hit_record(unreal.SystemLibrary.line_trace_single(world,
            point + unreal.Vector(0, 0, 650), point - unreal.Vector(0, 0, 1400),
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True))
        sample = {"index": index, "expected": point.to_tuple(), "hit": h}
        if not h:
            report["missing_floor"].append(sample)
            centers.append(None)
        else:
            sample["dz"] = h["point"][2] - point.z
            if abs(sample["dz"]) > 48:
                report["height_mismatches"].append(sample)
            centers.append(unreal.Vector(point.x, point.y, h["point"][2] + 99))
        report["samples"].append(sample)
    for index, (a, b) in enumerate(zip(centers, centers[1:])):
        if a is None or b is None:
            continue
        h = hit_record(unreal.SystemLibrary.capsule_trace_single(world, a, b, 42, 96,
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True))
        if h and not (h["normal"][2] > math.cos(math.radians(45)) and h["point"][2] < max(a.z, b.z) - 60):
            report["obstructions"].append({"index": index, **h})
    runtime = json.loads((OUT / "Route_Playtest.json").read_text())
    if runtime.get("stuck_location"):
        p = unreal.Vector(*runtime["stuck_location"])
        target = points[min(runtime["last_index"] + 1, len(points)-1)]
        target.z = p.z
        report["runtime_stuck_probe"] = hit_record(unreal.SystemLibrary.capsule_trace_single(
            world, p, target, 42, 96, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True))
    groups = defaultdict(list)
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if "L_IndustrialSlums_DistrictFinal" not in actor.get_level().get_path_name():
            continue
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            if not mesh:
                continue
            transform = component.get_world_transform()
            location = transform.translation.to_tuple()
            rotation = transform.rotation.rotator().to_tuple()
            scale = transform.scale3d.to_tuple()
            key = (mesh.get_path_name(), tuple(round(v, 2) for v in (*location, *rotation, *scale)))
            groups[key].append({"actor": actor.get_actor_label(), "actor_path": actor.get_path_name(),
                                "component": component.get_name(), "class": actor.get_class().get_name()})
    report["duplicate_mesh_transforms"] = [{"mesh": k[0], "transform": k[1], "components": v}
                                           for k, v in groups.items() if len(v) > 1]
    report["success"] = not report["missing_floor"] and not report["height_mismatches"] and not report["obstructions"]
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    (OUT / "Route_Clearance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("HOSPITAL_CLEARANCE " + str(report["success"]))
