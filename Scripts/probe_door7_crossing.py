"""Check capsule clearance through the existing framed BP_Door7, without saving."""

import json
import math
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT = ROOT / "Saved/MansionConnection/Door7_Crossing_Probe.json"
LABEL = "BP_Door7"


def vec(values):
    return unreal.Vector(float(values[0]), float(values[1]), float(values[2]))


def trace_capsule(world, start, end):
    result = unreal.SystemLibrary.capsule_trace_single(
        world, start, end, 42.0, 96.0, unreal.TraceTypeQuery.ECC_VISIBILITY,
        False, [], unreal.DrawDebugTrace.NONE, True,
    )
    hit = result.to_tuple() if result else None
    if not hit or not hit[0]:
        return {"blocked": False, "actor_path": None, "component": None}
    actor = hit[9] if len(hit) > 9 else None
    component = hit[10] if len(hit) > 10 else None
    return {
        "blocked": True,
        "actor": actor.get_actor_label() if actor else None,
        "actor_path": actor.get_path_name() if actor else None,
        "component": component.get_name() if component else None,
        "impact_point": list(hit[5].to_tuple()) if hit[5] else None,
    }


def floor_trace(world, point):
    start = point + unreal.Vector(0.0, 0.0, 500.0)
    end = point - unreal.Vector(0.0, 0.0, 800.0)
    result = unreal.SystemLibrary.line_trace_single(
        world, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY,
        False, [], unreal.DrawDebugTrace.NONE, True,
    )
    hit = result.to_tuple() if result else None
    if not hit or not hit[0]:
        return None
    return {"point": hit[5], "actor": hit[9].get_actor_label() if hit[9] else None}


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
door = next((actor for actor in actors.get_all_level_actors()
             if actor.get_actor_label() == LABEL), None)
if not door:
    raise RuntimeError(f"Could not find the placed actor {LABEL}")

leaves = {component.get_name(): component for component in
          door.get_components_by_class(unreal.StaticMeshComponent)}
left, right = leaves.get("SM_Door02_D"), leaves.get("SM_Door02_E")
if not left or not right:
    raise RuntimeError(f"{LABEL} does not contain both authored door leaves")
original_left = left.get_editor_property("relative_rotation")
original_right = right.get_editor_property("relative_rotation")
location = door.get_actor_location()
yaw = door.get_actor_rotation().yaw
angle = math.radians(yaw)
# Local Y is the passage normal because the two leaves are spaced along local X.
normal = unreal.Vector(-math.sin(angle), math.cos(angle), 0.0)
report = {
    "map": MAP,
    "door_label": door.get_actor_label(),
    "door_path": door.get_path_name(),
    "door_location": list(location.to_tuple()),
    "door_yaw": yaw,
    "saved_map_modified": False,
    "tests": [],
}

try:
    for distance in (180.0, 220.0, 260.0):
        side_a = location + normal * distance
        side_b = location - normal * distance
        floor_a = floor_trace(world, side_a)
        floor_b = floor_trace(world, side_b)
        item = {"offset_cm": distance, "side_a_floor": None, "side_b_floor": None}
        if not floor_a or not floor_b:
            item["error"] = "No floor on both sides of the doorway"
            report["tests"].append(item)
            continue
        item["side_a_floor"] = {"actor": floor_a["actor"], "point": list(floor_a["point"].to_tuple())}
        item["side_b_floor"] = {"actor": floor_b["actor"], "point": list(floor_b["point"].to_tuple())}
        # Use the live player's standing floor clearance so the capsule does
        # not begin overlapped with the floor that supports its bottom.
        start = floor_a["point"] + unreal.Vector(0.0, 0.0, 98.2)
        end = floor_b["point"] + unreal.Vector(0.0, 0.0, 98.2)
        item["closed_sweep"] = trace_capsule(world, start, end)
        left_open = unreal.Rotator(
            pitch=original_left.pitch, yaw=original_left.yaw + 90.0, roll=original_left.roll
        )
        right_open = unreal.Rotator(
            pitch=original_right.pitch, yaw=original_right.yaw - 90.0, roll=original_right.roll
        )
        left.set_relative_rotation(left_open, False, True)
        right.set_relative_rotation(right_open, False, True)
        item["open_sweep"] = trace_capsule(world, start, end)
        item["left_relative_rotation_open"] = list(left.get_editor_property("relative_rotation").to_tuple())
        item["right_relative_rotation_open"] = list(right.get_editor_property("relative_rotation").to_tuple())
        item["gate_works"] = item["closed_sweep"]["blocked"] and not item["open_sweep"]["blocked"]
        report["tests"].append(item)
        left.set_relative_rotation(original_left, False, True)
        right.set_relative_rotation(original_right, False, True)
finally:
    left.set_relative_rotation(original_left, False, True)
    right.set_relative_rotation(original_right, False, True)
    report["gate_clearance_passes"] = sum(bool(item.get("gate_works")) for item in report["tests"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("DOOR7_CROSSING_PROBE " + json.dumps({
        "passes": report["gate_clearance_passes"],
        "trials": len(report["tests"]),
        "saved_map_modified": False,
        "report": str(OUT),
    }))
    unreal.SystemLibrary.quit_editor()
