"""Find capsule-clear walking routes between mission room approaches.

Loads the connected level in an editor commandlet, samples floor support and
player-capsule clearance on a coarse XY grid, then runs A* between the saved
candidate interaction approaches. Selected door actors are ignored to model
their open states. This is collision/path evidence, not a rendered PIE test.
"""

import heapq
import json
import math
import time
from collections import Counter
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
SITES_PATH = ROOT / "Saved/MansionConnection/Mission_EastEntry_Candidate_Clearance.json"
REPORT_PATH = ROOT / "Saved/MansionConnection/Mission_Entrance_Frontier_Blockers.json"
STEP = 50.0
X_MIN, X_MAX = -71600.0, -68700.0
Y_MIN, Y_MAX = -89600.0, -85200.0
TRACE_TOP, TRACE_BOTTOM = 1100.0, 350.0
CAPSULE_RADIUS, CAPSULE_HALF_HEIGHT = 42.0, 96.0

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
by_label = {actor.get_actor_label(): actor for actor in actor_subsystem.get_all_level_actors()}
door_to_ignore = by_label.get("BP_Door7")
main_door_to_ignore = by_label.get("SM_Door02_E2")
foyer_passage_doors_to_ignore = [
    actor for actor in (by_label.get("SM_Door02_E"), by_label.get("BP_Door10")) if actor
]
site_data = json.loads(SITES_PATH.read_text(encoding="utf-8"))
site_by_name = {entry["name"]: entry for entry in site_data["sites"]}
node_cache = {}
edge_cache = {}
trace_count = 0
unsupported_floor_samples = 0
capsule_node_blockers = Counter()
blocked_edge_actors = Counter()
blocked_edge_examples = []
slope_rejection_count = 0
started = time.monotonic()


def hit_tuple(hit):
    return hit.to_tuple() if hit else None


def key_for(x, y):
    return round((x - X_MIN) / STEP), round((y - Y_MIN) / STEP)


def location_for(key):
    return unreal.Vector(X_MIN + key[0] * STEP, Y_MIN + key[1] * STEP, 0.0)


def in_bounds(key):
    p = location_for(key)
    return X_MIN <= p.x <= X_MAX and Y_MIN <= p.y <= Y_MAX


def trace_floor(key, ignored_actors):
    global trace_count
    xy = location_for(key)
    hit = hit_tuple(unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(xy.x, xy.y, TRACE_TOP),
        unreal.Vector(xy.x, xy.y, TRACE_BOTTOM),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        ignored_actors,
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    trace_count += 1
    if not hit or not hit[0]:
        return None
    position, normal, actor = hit[5], hit[7], hit[9]
    if position.z < TRACE_BOTTOM or position.z > TRACE_TOP:
        return None
    if normal.z < 0.65:
        return None
    return {
        "position": unreal.Vector(xy.x, xy.y, position.z + CAPSULE_HALF_HEIGHT + 1.0),
        "floor_z": position.z,
        "normal_z": normal.z,
        "actor": actor.get_actor_label() if actor else None,
    }


def get_node(key, ignored_actors):
    global trace_count, unsupported_floor_samples
    if not in_bounds(key):
        return None
    cache_key = (key, tuple(sorted(actor.get_path_name() for actor in ignored_actors if actor)))
    if cache_key in node_cache:
        return node_cache[cache_key]
    # Keep the stair mesh as the floor-support source while excluding it from
    # the capsule clearance query below. This isolates a solid-collider issue.
    floor = trace_floor(key, [])
    if not floor:
        unsupported_floor_samples += 1
        node_cache[cache_key] = None
        return None
    position = floor["position"]
    hit = hit_tuple(unreal.SystemLibrary.capsule_trace_single(
        world,
        position,
        position + unreal.Vector(0.0, 0.0, 0.1),
        CAPSULE_RADIUS,
        CAPSULE_HALF_HEIGHT,
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        ignored_actors,
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    trace_count += 1
    if hit and hit[0]:
        actor = hit[9]
        capsule_node_blockers[actor.get_actor_label() if actor else "<no actor>"] += 1
    node = None if hit and hit[0] else floor
    node_cache[cache_key] = node
    return node


def nearest_nodes(points, ignored_actors):
    results = []
    for entry in points:
        location = entry["location"]
        source = unreal.Vector(*location)
        center_key = key_for(source.x, source.y)
        choices = []
        for radius in range(0, 4):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy)) != radius:
                        continue
                    key = (center_key[0] + dx, center_key[1] + dy)
                    node = get_node(key, ignored_actors)
                    if not node or abs(node["floor_z"] + CAPSULE_HALF_HEIGHT + 1.0 - source.z) > 115.0:
                        continue
                    p = node["position"]
                    choices.append((math.hypot(p.x - source.x, p.y - source.y), key, node))
            if choices:
                break
        if choices:
            choices.sort(key=lambda value: value[0])
            distance, key, node = choices[0]
            results.append({
                "key": key,
                "position": node["position"],
                "source": entry.get("label", "candidate"),
                "source_distance_cm": distance,
                "floor_actor": node["actor"],
            })
    return results


def clear_edge(a_key, b_key, a_node, b_node, ignored_actors):
    global trace_count, slope_rejection_count
    cache_key = (a_key, b_key, tuple(sorted(actor.get_path_name() for actor in ignored_actors if actor)))
    if cache_key in edge_cache:
        return edge_cache[cache_key]
    if a_key[0] > b_key[0] or (a_key[0] == b_key[0] and a_key[1] > b_key[1]):
        return clear_edge(b_key, a_key, b_node, a_node, ignored_actors)
    dx, dy = (b_key[0] - a_key[0]) * STEP, (b_key[1] - a_key[1]) * STEP
    horizontal = math.hypot(dx, dy)
    delta_z = abs(a_node["position"].z - b_node["position"].z)
    if delta_z > (70.0 if horizontal > STEP else 60.0):
        slope_rejection_count += 1
        edge_cache[cache_key] = False
        return False
    hit = hit_tuple(unreal.SystemLibrary.capsule_trace_single(
        world,
        a_node["position"],
        b_node["position"],
        CAPSULE_RADIUS,
        CAPSULE_HALF_HEIGHT,
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        ignored_actors,
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    trace_count += 1
    clear = not bool(hit and hit[0])
    if not clear:
        actor = hit[9]
        label = actor.get_actor_label() if actor else "<no actor>"
        blocked_edge_actors[label] += 1
        if len(blocked_edge_examples) < 30:
            blocked_edge_examples.append({
                "blocker": label,
                "from": list(a_node["position"].to_tuple()),
                "to": list(b_node["position"].to_tuple()),
                "impact": list(hit[5].to_tuple()),
            })
    edge_cache[cache_key] = clear
    return clear


NEIGHBORS = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1),
]


def find_path(start_candidates, goal_candidates, ignored_actors):
    starts = nearest_nodes(start_candidates, ignored_actors)
    goals = nearest_nodes(goal_candidates, ignored_actors)
    goal_keys = {candidate["key"] for candidate in goals}
    if not starts or not goals:
        return None, starts, goals, 0
    best_cost = {}
    previous = {}
    origin = {}
    queue = []
    for candidate in starts:
        key = candidate["key"]
        best_cost[key] = 0.0
        origin[key] = candidate
        heuristic = min(math.hypot(key[0] - goal["key"][0], key[1] - goal["key"][1]) for goal in goals)
        heapq.heappush(queue, (heuristic, 0.0, key))
    expansions = 0
    reached = None
    explored = []
    while queue:
        _, current_cost, current = heapq.heappop(queue)
        if current_cost > best_cost.get(current, float("inf")) + 1e-6:
            continue
        if current in goal_keys:
            reached = current
            break
        current_node = get_node(current, ignored_actors)
        if not current_node:
            continue
        expansions += 1
        if len(explored) < 250:
            explored.append({
                "xy_index": list(current),
                "position": list(current_node["position"].to_tuple()),
                "floor_actor": current_node["actor"],
            })
        if expansions % 500 == 0:
            unreal.log(f"MANSION_PATH_PROGRESS expansions={expansions} traces={trace_count} elapsed={time.monotonic() - started:.1f}s")
        for ox, oy in NEIGHBORS:
            nxt = (current[0] + ox, current[1] + oy)
            next_node = get_node(nxt, ignored_actors)
            if not next_node:
                continue
            if ox and oy:
                side_x = (current[0] + ox, current[1])
                side_y = (current[0], current[1] + oy)
                side_x_node = get_node(side_x, ignored_actors)
                side_y_node = get_node(side_y, ignored_actors)
                if not side_x_node or not side_y_node:
                    continue
                if not clear_edge(current, side_x, current_node, side_x_node, ignored_actors):
                    continue
                if not clear_edge(current, side_y, current_node, side_y_node, ignored_actors):
                    continue
            if not clear_edge(current, nxt, current_node, next_node, ignored_actors):
                continue
            horizontal = STEP * (math.sqrt(2.0) if ox and oy else 1.0)
            move_cost = math.hypot(horizontal, next_node["position"].z - current_node["position"].z) + 10.0
            tentative = current_cost + move_cost
            if tentative >= best_cost.get(nxt, float("inf")):
                continue
            best_cost[nxt] = tentative
            previous[nxt] = current
            origin[nxt] = origin[current]
            heuristic = min(math.hypot(nxt[0] - goal["key"][0], nxt[1] - goal["key"][1]) for goal in goals) * STEP
            heapq.heappush(queue, (tentative + heuristic, tentative, nxt))

    if reached is None:
        return {
            "success": False,
            "explored": explored,
            "start_nodes": [
                {"label": item["source"], "xy_index": list(item["key"]), "position": list(item["position"].to_tuple()),
                 "floor_actor": item["floor_actor"], "source_distance_cm": item["source_distance_cm"]}
                for item in starts
            ],
            "goal_nodes": [
                {"label": item["source"], "xy_index": list(item["key"]), "position": list(item["position"].to_tuple()),
                 "floor_actor": item["floor_actor"], "source_distance_cm": item["source_distance_cm"]}
                for item in goals
            ],
        }, starts, goals, expansions
    keys = [reached]
    while keys[-1] in previous:
        keys.append(previous[keys[-1]])
    keys.reverse()
    path = []
    for key in keys:
        node = get_node(key, ignored_actors)
        path.append({
            "xy_index": list(key),
            "position": list(node["position"].to_tuple()),
            "floor_actor": node["actor"],
        })
    goal_source = next(candidate for candidate in goals if candidate["key"] == reached)
    length = sum(math.dist(path[index]["position"], path[index + 1]["position"]) for index in range(len(path) - 1))
    return {
        "success": True,
        "start_candidate": origin[reached]["source"],
        "goal_candidate": goal_source["source"],
        "length_cm": length,
        "node_count": len(path),
        "path": path,
    }, starts, goals, expansions


def candidates(site_name):
    site = site_by_name[site_name]
    options = [entry for entry in site["standing_options"] if not entry["blocked"]]
    clear_sight = [entry for entry in options if entry["interaction_sight_clear"]]
    selected = clear_sight if clear_sight else options
    return [
        {"location": entry["location"], "label": f"{site_name} approach {index + 1}", "clear_sight": entry["interaction_sight_clear"]}
        for index, entry in enumerate(selected)
    ]


entry_doors_to_ignore = [actor for actor in (
    main_door_to_ignore,
    by_label.get("SM_Door02_E"),
    by_label.get("SM_Door12"),
    by_label.get("SM_OuterStairs8"),
    by_label.get("SM_OuterStairs10"),
) if actor]
segments = [
    ("Front door to east interior floor 163 with both outer-stair colliders ignored", "Mansion front door", "East interior floor 163", entry_doors_to_ignore),
]
report = {
    "map": MAP,
    "method": {
        "grid_spacing_cm": STEP,
        "capsule_radius_cm": CAPSULE_RADIUS,
        "capsule_half_height_cm": CAPSULE_HALF_HEIGHT,
        "visibility_collision_channel": True,
        "entry_and_stair_actors_ignored_for_capsule_only": [actor.get_path_name() for actor in entry_doors_to_ignore],
        "warning": "Diagnostic only: tested door/stair actors remain possible floor-support sources but are ignored by capsule clearance; not a candidate shipping setting.",
    },
    "navigation_actors": [
        {"label": actor.get_actor_label(), "class": actor.get_class().get_name(), "path": actor.get_path_name()}
        for actor in actor_subsystem.get_all_level_actors()
        if any(token in actor.get_class().get_name().lower() for token in ("navmesh", "navigation"))
    ],
    "segments": [],
}

navmesh_report = {"available": False, "segments": []}
try:
    navigation_system = unreal.NavigationSystemV1.get_navigation_system(world)
    navmesh_report["available"] = bool(navigation_system)
    navmesh_report["navigation_system"] = navigation_system.get_class().get_name() if navigation_system else None
    if navigation_system:
        for name, start_name, goal_name, _ in segments:
            start_candidates = candidates(start_name)
            goal_candidates = candidates(goal_name)
            projected_starts = []
            projected_goals = []
            projection_extent = unreal.Vector(500.0, 500.0, 350.0)
            for role, entries, output in (("start", start_candidates, projected_starts), ("goal", goal_candidates, projected_goals)):
                for entry in entries:
                    location = unreal.Vector(*entry["location"])
                    projected = unreal.NavigationSystemV1.project_point_to_navigation(
                        world, location, None, None, projection_extent
                    )
                    if projected:
                        output.append({"label": entry["label"], "location": list(projected.to_tuple())})
            nav_segment = {
                "name": name,
                "projected_start_candidates": projected_starts,
                "projected_goal_candidates": projected_goals,
                "routes": [],
            }
            for start in projected_starts:
                for goal in projected_goals:
                    path = unreal.NavigationSystemV1.find_path_to_location_synchronously(
                        world,
                        unreal.Vector(*start["location"]),
                        unreal.Vector(*goal["location"]),
                        None,
                        None,
                    )
                    if not path:
                        continue
                    path_points = path.get_editor_property("path_points")
                    nav_segment["routes"].append({
                        "start": start,
                        "goal": goal,
                        "valid": path.is_valid(),
                        "partial": path.is_partial(),
                        "length_cm": path.get_path_length(),
                        "points": [list(point.to_tuple()) for point in path_points],
                    })
            nav_segment["success"] = any(route["valid"] and not route["partial"] for route in nav_segment["routes"])
            navmesh_report["segments"].append(nav_segment)
except Exception as error:
    navmesh_report["error"] = str(error)
report["navmesh"] = navmesh_report

for name, start_name, goal_name, ignored in segments:
    unreal.log(f"MANSION_PATH_START {name}")
    route, starts, goals, expansions = find_path(candidates(start_name), candidates(goal_name), ignored)
    report["segments"].append({
        "name": name,
        "success": bool(route and route.get("success")),
        "ignored_actor_paths": [actor.get_path_name() for actor in ignored if actor],
        "start_candidates": [item["source"] for item in starts],
        "goal_candidates": [item["source"] for item in goals],
        "expanded_nodes": expansions,
        "route": route,
    })
    unreal.log(f"MANSION_PATH_DONE {name} success={bool(route and route.get('success'))} expansions={expansions} traces={trace_count}")

report["trace_count"] = trace_count
report["elapsed_seconds"] = round(time.monotonic() - started, 2)
report["frontier_diagnostics"] = {
    "unsupported_floor_samples": unsupported_floor_samples,
    "capsule_node_blockers": dict(capsule_node_blockers.most_common()),
    "blocked_edge_actors": dict(blocked_edge_actors.most_common()),
    "blocked_edge_examples": blocked_edge_examples,
    "slope_rejection_count": slope_rejection_count,
}
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"MANSION_WALKABLE_PATH_REPORT {REPORT_PATH} {json.dumps({'traces': trace_count, 'elapsed': report['elapsed_seconds'], 'segments': [item['success'] for item in report['segments']]})}")
unreal.SystemLibrary.quit_editor()
