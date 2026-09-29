"""Resolve all current route audit hits to actor transforms and bounds."""
import json
from pathlib import Path

import unreal

ROOT = Path(r"F:\Carnival")
MAIN = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
AUDIT = ROOT / "Saved/WorldExpansion/Route_Collision_Audit.json"
OUT = ROOT / "Saved/WorldExpansion/Route_Hit_Actor_Transforms.json"
source = json.loads(AUDIT.read_text(encoding="utf-8"))
world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN)
if not world:
    raise RuntimeError("Could not load connected world for hit transform audit")


def actor_row(actor):
    row = {"label": actor.get_actor_label(), "path": actor.get_path_name(),
           "class": actor.get_class().get_name(),
           "location_cm": actor.get_actor_location().to_tuple(),
           "rotation_deg": actor.get_actor_rotation().to_tuple(),
           "scale": actor.get_actor_scale3d().to_tuple()}
    center, extent = actor.get_actor_bounds(False, True)
    row["bounds_center_cm"] = center.to_tuple()
    row["bounds_extent_cm"] = extent.to_tuple()
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component:
        mesh = component.get_editor_property("static_mesh")
        row["mesh"] = mesh.get_path_name() if mesh else None
    return row


def trace_hit(start, end, capsule=False):
    if capsule:
        hit = unreal.SystemLibrary.capsule_trace_single(
            world, start, end, 42.0, 96.0, unreal.TraceTypeQuery.ECC_VISIBILITY,
            False, [], unreal.DrawDebugTrace.NONE, True)
    else:
        hit = unreal.SystemLibrary.line_trace_single(
            world, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY,
            False, [], unreal.DrawDebugTrace.NONE, True)
    values = hit.to_tuple() if hit else None
    if not values or not values[0] or not values[9]:
        return None
    actor = actor_row(values[9])
    return {"point_cm": values[5].to_tuple(), "normal": values[7].to_tuple(),
            "actor": actor}


actors = {}
issues = []


def register_issue(route, kind, index, expected_hit, trace):
    actor = trace["actor"] if trace else None
    actor_key = actor["path"] if actor else None
    if actor and actor_key not in actors:
        actors[actor_key] = actor
    issues.append({"route": route, "kind": kind, "index": index,
                   "audit_hit": expected_hit, "resolved_trace": trace,
                   "actor_key": actor_key})


for route in source.get("routes", []):
    route_name = route["name"]
    # These values match the static audit's route-specific trace ranges.
    high, low = (250.0, 150.0) if route_name.startswith(("R10_stair", "R11_", "R12_")) else (400.0, 180.0)
    for mismatch in route.get("height_mismatches", []):
        index = mismatch["index"]
        sample = route["samples"][index]
        x, y, z = sample["expected_cm"]
        trace = trace_hit(unreal.Vector(x, y, z + high),
                          unreal.Vector(x, y, z - low), False)
        register_issue(route_name, "height_mismatch", index, mismatch.get("hit"), trace)

    for obstruction in route.get("capsule_obstructions", []):
        index = obstruction["segment"]
        a, b = route["samples"][index], route["samples"][index + 1]
        if not a.get("floor_hit") or not b.get("floor_hit"):
            continue
        start = unreal.Vector(a["expected_cm"][0], a["expected_cm"][1],
                              a["floor_hit"]["point_cm"][2] + 96.0)
        end = unreal.Vector(b["expected_cm"][0], b["expected_cm"][1],
                            b["floor_hit"]["point_cm"][2] + 96.0)
        trace = trace_hit(start, end, True)
        register_issue(route_name, "capsule_obstruction", index, obstruction, trace)

OUT.write_text(json.dumps({"map": MAIN, "method": "Replayed audit hit traces; unique actors include world bounds and mesh transforms.",
                           "actor_count": len(actors), "actors": list(actors.values()),
                           "issues": issues}, indent=2), encoding="utf-8")
unreal.log("WORLD_EXPANSION_HIT_TRANSFORMS " + json.dumps({
    "actor_count": len(actors), "issue_count": len(issues), "output": str(OUT)}))
unreal.SystemLibrary.quit_editor()
