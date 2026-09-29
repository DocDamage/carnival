"""Capture actor bounds near route trace anomalies for collision triage."""
import json
import math
from pathlib import Path

import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/Route_Overlap_Inspection.json"
MAIN = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REGION = json.loads((ROOT / "Saved/WorldExpansion/Region_Authoring.json").read_text(encoding="utf-8"))


def catmull(controls, step=700.0):
    points = []
    for i in range(len(controls) - 1):
        a, b = controls[max(i - 1, 0)], controls[i]
        d, e = controls[i + 1], controls[min(i + 2, len(controls) - 1)]
        count = max(2, int(math.ceil(math.dist(b, d) / step)))
        for j in range(count):
            t = j / float(count)
            t2, t3 = t * t, t * t * t
            points.append(tuple(0.5 * (2 * b[k] + (-a[k] + d[k]) * t
                                  + (2 * a[k] - 5 * b[k] + 4 * d[k] - e[k]) * t2
                                  + (-a[k] + 3 * b[k] - 3 * d[k] + e[k]) * t3)
                                for k in range(3)))
    points.append(tuple(controls[-1]))
    return points


def compact_actor(actor):
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    row = {"label": actor.get_actor_label(), "path": actor.get_path_name(),
           "class": actor.get_class().get_name(), "location_cm": list(loc.to_tuple()),
           "rotation": [rot.pitch, rot.yaw, rot.roll], "scale": list(scale.to_tuple())}
    try:
        origin, extent = actor.get_actor_bounds(True)
        row["bounds_origin_cm"] = list(origin.to_tuple())
        row["bounds_extent_cm"] = list(extent.to_tuple())
    except Exception as exc:
        row["bounds_error"] = str(exc)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component:
        mesh = component.get_editor_property("static_mesh")
        row["mesh"] = mesh.get_path_name() if mesh else None
    return row


report = {"map": MAIN, "targets": [], "key_actors": [], "errors": []}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN)
    if not world:
        raise RuntimeError("Could not load the main map")
    controls = REGION["outer_route_spine"]["controls_cm"]
    curve = catmull(controls)
    centers = [tuple((a[k] + b[k]) * 0.5 for k in range(3)) for a, b in zip(curve, curve[1:])]
    targets = [("outer_0", centers[0]), ("outer_100", centers[100]),
               ("outer_309", centers[309]), ("outer_340", centers[340]),
               ("outer_400", centers[400]), ("outer_434", centers[434]),
               ("hospital_route_420", (95024.3, 122469.96, 664.0)),
               ("hospital_route_421", (95089.5, 123009.63, 664.0)),
               ("hospital_route_424", (95277.9, 124554.55, 664.0)),
               ("hospital_route_426", (95387.8, 125507.0, 664.0)),
               ("stair_24", (-27000.0, -17672.9166667, 122.0)),
               ("stair_50", (-27000.0, -16264.5833333, -398.0)),
               ("stair_109", (-27000.0, -13068.75, -1578.0)),
               ("r12_0", (-6750.0, -10750.0, -1832.67)),
               ("r12_1", (-6250.0, -10250.0, -1932.67))]
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    for actor in actors:
        try:
            label = actor.get_actor_label().lower()
            if "factory-gate facade" in label or "hospital entrance" in label:
                report["key_actors"].append(compact_actor(actor))
        except Exception:
            pass
    for name, target in targets:
        nearby = []
        for actor in actors:
            try:
                loc = actor.get_actor_location()
                distance_xy = math.hypot(loc.x - target[0], loc.y - target[1])
                distance_z = abs(loc.z - target[2])
                if distance_xy <= 1100 and distance_z <= 800:
                    nearby.append((distance_xy + distance_z * 0.35, actor))
            except Exception:
                pass
        nearby.sort(key=lambda pair: pair[0])
        report["targets"].append({"name": name, "expected_cm": list(target),
                                  "actors": [compact_actor(actor) for _, actor in nearby[:14]]})
except Exception as exc:
    report["errors"].append(repr(exc))
finally:
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.SystemLibrary.quit_editor()
