"""Static floor and capsule trace audit for the authored world expansion."""
import json
import math
import traceback
from pathlib import Path

import unreal

ROOT = Path(r"F:\Carnival")
MAIN = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT = ROOT / "Saved/WorldExpansion/Route_Collision_Audit.json"
REGION = json.loads((ROOT / "Saved/WorldExpansion/Region_Authoring.json").read_text(encoding="utf-8"))
CONNECTIONS = {item["id"]: item for item in REGION["connections"]}


def catmull(controls, step=800.0):
    points = []
    for i in range(len(controls) - 1):
        a, b = controls[max(i - 1, 0)], controls[i]
        d, e = controls[i + 1], controls[min(i + 2, len(controls) - 1)]
        count = max(2, int(math.ceil(math.dist(b, d) / step)))
        for j in range(count):
            t = j / float(count)
            t2, t3 = t * t, t * t * t
            points.append(tuple(
                0.5 * (2 * b[k] + (-a[k] + d[k]) * t
                       + (2 * a[k] - 5 * b[k] + 4 * d[k] - e[k]) * t2
                       + (-a[k] + 3 * b[k] - 3 * d[k] + e[k]) * t3)
                for k in range(3)
            ))
    points.append(tuple(controls[-1]))
    return points


def surface_segment_centers(controls, curve_step, target_segment, thickness):
    """Match the authored route boxes and return the center of each top face."""
    curve_points = catmull(controls, curve_step)
    result = []
    for a, b in zip(curve_points, curve_points[1:]):
        distance = math.dist(a, b)
        count = 1 if target_segment is None else max(1, int(math.ceil(distance / target_segment)))
        for j in range(count):
            t0, t1 = j / float(count), (j + 1) / float(count)
            p = tuple(a[k] * (1 - t0) + b[k] * t0 for k in range(3))
            q = tuple(a[k] * (1 - t1) + b[k] * t1 for k in range(3))
            center = tuple((p[k] + q[k]) * 0.5 for k in range(3))
            horizontal = max(1.0, math.hypot(q[0] - p[0], q[1] - p[1]))
            pitch = math.atan2(q[2] - p[2], horizontal)
            top_z = center[2] + thickness * 0.5 * math.cos(pitch)
            result.append((center[0], center[1], top_z))
    return result


def linear(a, b, spacing=250.0):
    length = math.dist(a, b)
    count = max(1, int(math.ceil(length / spacing)))
    return [tuple(a[k] * (1 - i / count) + b[k] * (i / count) for k in range(3))
            for i in range(count + 1)]


def hit_record(hit):
    values = hit.to_tuple() if hit else None
    if not values or not values[0]:
        return None
    actor = values[9]
    return {
        "point_cm": list(values[5].to_tuple()) if values[5] else None,
        "normal": list(values[7].to_tuple()) if values[7] else None,
        "actor": actor.get_actor_label() if actor else None,
        "actor_path": actor.get_path_name() if actor else None,
    }


def floor_at(world, point, low=180.0, high=400.0):
    x, y, z = point
    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, z + high),
        unreal.Vector(x, y, z - low),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
    )
    return hit_record(hit)


def capsule_between(world, start, end):
    hit = unreal.SystemLibrary.capsule_trace_single(
        world,
        start,
        end,
        42.0,
        96.0,
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
    )
    return hit_record(hit)


def summarize_route(world, name, points, test_capsule=True, mismatch_tolerance=55.0,
                    trace_high=400.0, trace_low=180.0):
    result = {"name": name, "sample_count": len(points), "floor_missing": [],
              "height_mismatches": [], "capsule_obstructions": [],
              "route_surface_capsule_obstructions": [], "samples": []}
    centers = []
    route_centers = []
    for index, point in enumerate(points):
        hit = floor_at(world, point, low=trace_low, high=trace_high)
        row = {"index": index, "expected_cm": list(point), "floor_hit": hit}
        route_centers.append(unreal.Vector(point[0], point[1], point[2] + 96.0))
        if not hit:
            result["floor_missing"].append(index)
            centers.append(None)
        else:
            delta = hit["point_cm"][2] - point[2]
            row["height_delta_cm"] = delta
            if abs(delta) > mismatch_tolerance:
                result["height_mismatches"].append({"index": index, "delta_cm": delta, "hit": hit})
            centers.append(unreal.Vector(point[0], point[1], hit["point_cm"][2] + 96.0))
        result["samples"].append(row)

    if test_capsule:
        for index, (a, b) in enumerate(zip(centers, centers[1:])):
            if a is None or b is None:
                continue
            horizontal = math.hypot(b.x - a.x, b.y - a.y)
            vertical = abs(b.z - a.z)
            if vertical > max(45.0, horizontal * 0.35):
                continue
            hit = capsule_between(world, a, b)
            if hit:
                point = hit["point_cm"]
                normal = hit["normal"]
                floor_contact = bool(normal and normal[2] > math.cos(math.radians(45))
                                     and point and point[2] < max(a.z, b.z) - 55.0)
                if not floor_contact:
                    result["capsule_obstructions"].append({"segment": index, **hit})

        for index, (a, b) in enumerate(zip(route_centers, route_centers[1:])):
            horizontal = math.hypot(b.x - a.x, b.y - a.y)
            vertical = abs(b.z - a.z)
            if vertical > max(45.0, horizontal * 0.35):
                continue
            hit = capsule_between(world, a, b)
            if hit:
                point = hit["point_cm"]
                normal = hit["normal"]
                floor_contact = bool(normal and normal[2] > math.cos(math.radians(45))
                                     and point and point[2] < max(a.z, b.z) - 55.0)
                if not floor_contact:
                    result["route_surface_capsule_obstructions"].append(
                        {"segment": index, **hit})

    result["static_trace_clear"] = not (result["floor_missing"] or result["height_mismatches"]
                                         or result["capsule_obstructions"])
    result["authored_surface_capsule_clear"] = not result["route_surface_capsule_obstructions"]
    return result


report = {
    "map": MAIN,
    "method": "Editor-world visibility line/capsule traces sampled at authored route-box centers; static geometry evidence only, not PIE/player traversal.",
    "capsule_radius_cm": 42.0,
    "capsule_half_height_cm": 96.0,
    "routes": [],
    "errors": [],
}

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN)
    if not world:
        raise RuntimeError("Could not load the connected Carnival map")

    outer = REGION.get("outer_route_spine", {}).get("controls_cm")
    if outer:
        # The alignment repair writes one box between each 700 cm Catmull point.
        report["routes"].append(summarize_route(
            world, "R03-R06_outer_surface_spine",
            surface_segment_centers(outer, 700.0, None, 45.0)))

    for connection_id in ("R09", "R10"):
        connection = CONNECTIONS[connection_id]
        controls = connection["route"].get("controls_cm", [])
        if controls:
            target = 600.0 if connection_id == "R09" else 500.0
            report["routes"].append(summarize_route(
                world, connection_id + "_surface",
                surface_segment_centers(controls, 800.0, target, 40.0)))

    stair = CONNECTIONS["R10"]["stair"]
    step_run = stair["horizontal_length_m"] * 100.0 / stair["step_count"]
    step_rise = stair["vertical_drop_m"] * 100.0 / stair["step_count"]
    stair_points = [
        (stair["start_cm"][0], stair["start_cm"][1] + (index + 0.5) * step_run,
         stair["start_cm"][2] - index * step_rise + 2.0)
        for index in range(stair["step_count"])
    ]
    report["routes"].append(summarize_route(world, "R10_stair_step_support", stair_points,
                                             test_capsule=True, mismatch_tolerance=28.0,
                                             trace_high=250.0, trace_low=150.0))

    for connection_id in ("R11", "R12"):
        route = CONNECTIONS[connection_id]["route"]
        start, end = route["start_cm"], route["end_cm"]
        count = max(1, int(math.ceil(math.dist(start, end) / 900.0)))
        points = []
        for index in range(count):
            t0, t1 = index / float(count), (index + 1) / float(count)
            p = tuple(start[k] * (1 - t0) + end[k] * t0 for k in range(3))
            q = tuple(start[k] * (1 - t1) + end[k] * t1 for k in range(3))
            center = tuple((p[k] + q[k]) * 0.5 for k in range(3))
            horizontal = max(1.0, math.hypot(q[0] - p[0], q[1] - p[1]))
            pitch = math.atan2(q[2] - p[2], horizontal)
            points.append((center[0], center[1], center[2] + 17.5 * math.cos(pitch)))
        report["routes"].append(summarize_route(
            world, connection_id + "_interior_tunnel", points,
            trace_high=250.0, trace_low=150.0))

    report["success"] = all(item["static_trace_clear"] for item in report["routes"])
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("WORLD_EXPANSION_COLLISION_AUDIT " + json.dumps({
        "success": report.get("success"),
        "routes": {item["name"]: {
            "samples": item["sample_count"],
            "missing_floor": len(item["floor_missing"]),
            "height_mismatches": len(item["height_mismatches"]),
        "capsule_obstructions": len(item["capsule_obstructions"]),
        "route_surface_capsule_obstructions": len(item["route_surface_capsule_obstructions"]),
        } for item in report["routes"]},
        "errors": report["errors"],
    }))
    unreal.SystemLibrary.quit_editor()
