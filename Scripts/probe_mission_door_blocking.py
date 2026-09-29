"""Find a transient BP_Door02 placement that blocks and then clears the live room route."""

import json
import math
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
DOOR_CLASS = "/Game/Mansion/Mesh/Assets/Doors/BP_Door02.BP_Door02_C"
ROUTES = ROOT / "Saved/MansionConnection/Mission_Room_Routes.json"
OUT = ROOT / "Saved/MansionConnection/Mission_Door_Gate_Probe.json"
SEGMENT_NAME = "Study to music room table"


def vector(values):
    return unreal.Vector(float(values[0]), float(values[1]), float(values[2]))


def capsule_trace(world, start, end, half_height=96.0):
    result = unreal.SystemLibrary.capsule_trace_single(
        world, start, end, 42.0, half_height,
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True,
    )
    value = result.to_tuple() if result else None
    if not value or not value[0]:
        return {"blocked": False, "actor": None, "actor_path": None, "component_path": None}
    actor = value[9]
    component = value[10] if len(value) > 10 else None
    return {"blocked": True, "actor": actor.get_actor_label() if actor else None,
            "actor_path": actor.get_path_name() if actor else None,
            "component": component.get_name() if component else None,
            "component_path": component.get_path_name() if component else None,
            "hit_location": list(value[5].to_tuple()) if value[5] else None}


def component_transform(component):
    transform = component.get_world_transform()
    return {
        "location": list(transform.translation.to_tuple()),
        "rotation": list(transform.rotation.rotator().to_tuple()),
        "relative_rotation": list(component.get_editor_property("relative_rotation").to_tuple()),
        "collision_enabled": str(component.get_collision_enabled()),
    }


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")
report = {"map": MAP, "segment": SEGMENT_NAME, "saved_map_modified": False, "trials": []}
route_report = json.loads(ROUTES.read_text(encoding="utf-8"))
segment = next(row for row in route_report["segments"] if row["name"] == SEGMENT_NAME)
path = segment["route"]["path"]
door_class = unreal.load_class(None, DOOR_CLASS)
if not door_class:
    raise RuntimeError(f"Could not load {DOOR_CLASS}")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for index, (a, b) in enumerate(zip(path, path[1:])):
    pa, pb = vector(a["position"]), vector(b["position"])
    delta = pb - pa
    distance = math.sqrt(delta.x * delta.x + delta.y * delta.y)
    if distance < 45.0:
        continue
    direction = unreal.Vector(delta.x / distance, delta.y / distance, 0.0)
    center = (pa + pb) * .5
    start = center - direction * 220.0
    end = center + direction * 220.0
    baseline = capsule_trace(world, start, end)
    if baseline["blocked"]:
        continue

    path_yaw = math.degrees(math.atan2(direction.y, direction.x))
    # BP_Door02 spaces the two leaves along local X, so its frame plane faces
    # local Y and the actor yaw must be perpendicular to the crossing direction.
    yaw = path_yaw - 90.0
    door = actors.spawn_actor_from_class(door_class, unreal.Vector(center.x, center.y, center.z - 96.0),
                                         unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    if not door:
        continue
    leaves = {component.get_name(): component for component in door.get_components_by_class(unreal.StaticMeshComponent)}
    left = leaves.get("SM_Door02_D")
    right = leaves.get("SM_Door02_E")
    trial = {
        "route_edge_index": index,
        "floor_actor": a.get("floor_actor"),
        "center": list(center.to_tuple()),
        "door_location": list(door.get_actor_location().to_tuple()),
        "door_path": door.get_path_name(),
        "door_rotation": list(door.get_actor_rotation().to_tuple()),
        "door_yaw": yaw,
        "baseline_sweep": baseline,
        "leaf_components_found": [left is not None, right is not None],
    }
    if left and right:
        trial["leaf_component_state"] = []
        for component in (left, right):
            relative_location = component.get_editor_property("relative_location")
            relative_rotation = component.get_editor_property("relative_rotation")
            mesh = component.get_editor_property("static_mesh")
            trial["leaf_component_state"].append({
                "name": component.get_name(),
                "relative_location": list(relative_location.to_tuple()),
                "relative_rotation": list(relative_rotation.to_tuple()),
                "collision_enabled": str(component.get_collision_enabled()),
                "mesh": mesh.get_path_name() if mesh else None,
                "world_transform_before": component_transform(component),
            })
        trial["closed_sweep"] = capsule_trace(world, start, end)
        closed_left = left.get_editor_property("relative_rotation")
        closed_right = right.get_editor_property("relative_rotation")
        trial["closed_leaf_rotations"] = [list(closed_left.to_tuple()), list(closed_right.to_tuple())]
        open_variants = []
        # Start at the same 90 degree angle as ACarnivalMissionInteractionActor.
        for angle in (90.0, 70.0, 110.0, 130.0, 150.0):
            for left_sign, right_sign in ((1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0)):
                left_rotation = unreal.Rotator(pitch=closed_left.pitch, yaw=closed_left.yaw + left_sign * angle,
                                               roll=closed_left.roll)
                right_rotation = unreal.Rotator(pitch=closed_right.pitch, yaw=closed_right.yaw + right_sign * angle,
                                                roll=closed_right.roll)
                # Use the scene-component transform API so physics/query state is
                # updated with the transform, matching the native interaction actor.
                left.set_relative_rotation(left_rotation, False, True)
                right.set_relative_rotation(right_rotation, False, True)
                result = capsule_trace(world, start, end)
                open_variants.append({"angle": angle, "leaf_signs": [left_sign, right_sign], "sweep": result,
                                      "left": component_transform(left), "right": component_transform(right)})
                if not result["blocked"]:
                    break
            if any(not row["sweep"]["blocked"] for row in open_variants):
                break
        trial["open_variants"] = open_variants
        trial["rotation_opens_clearance"] = any(not row["sweep"]["blocked"] for row in open_variants)
        if not trial["rotation_opens_clearance"]:
            left.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            right.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            trial["collision_after_disable"] = [str(left.get_collision_enabled()), str(right.get_collision_enabled())]
            trial["left_after_disable"] = component_transform(left)
            trial["right_after_disable"] = component_transform(right)
            trial["open_sweep_without_leaf_collision"] = capsule_trace(world, start, end)
        trial["usable_gate"] = bool(trial["closed_sweep"]["blocked"]
                                    and (trial["rotation_opens_clearance"]
                                         or not trial["open_sweep_without_leaf_collision"]["blocked"]))
    actors.destroy_actor(door)
    report["trials"].append(trial)

report["usable_gate_candidates"] = [row for row in report["trials"] if row.get("usable_gate")]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("MISSION_DOOR_GATE_PROBE " + json.dumps({
    "route_edges_tested": len(report["trials"]),
    "usable_candidates": len(report["usable_gate_candidates"]),
    "report": str(OUT),
}))
unreal.SystemLibrary.quit_editor()
