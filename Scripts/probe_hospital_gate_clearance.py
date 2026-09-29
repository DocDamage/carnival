"""Find an exterior capsule-clear approach through the saved hospital facade."""
import json
import math
import traceback
from pathlib import Path

import unreal

ROOT = Path(r"F:\Carnival")
MAIN = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT = ROOT / "Saved/WorldExpansion/Hospital_Gate_Clearance_Probe.json"
TARGET_LABEL = "Abandoned Hospital Factory-Gate Facade"


def hit_data(hit):
    if not hit:
        return None
    row = hit.to_dict()
    actor = row.get("hit_actor")
    point = row.get("impact_point")
    normal = row.get("impact_normal")
    return {"blocking": bool(row.get("blocking_hit")),
            "initial_overlap": bool(row.get("initial_overlap")),
            "actor": actor.get_actor_label() if actor else None,
            "path": actor.get_path_name() if actor else None,
            "point_cm": list(point.to_tuple()) if point else None,
            "normal": list(normal.to_tuple()) if normal else None}


report = {"map": MAIN, "success": False, "gate": None, "sweeps": [], "errors": []}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN)
    if not world:
        raise RuntimeError("Could not load the Carnival map")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    gate = next((actor for actor in actors if actor.get_actor_label() == TARGET_LABEL), None)
    if not gate:
        raise RuntimeError("Saved hospital factory gate was not found")
    origin = gate.get_actor_location()
    yaw = math.radians(gate.get_actor_rotation().yaw)
    forward = unreal.Vector(math.cos(yaw), math.sin(yaw), 0.0)
    side = unreal.Vector(-math.sin(yaw), math.cos(yaw), 0.0)
    report["gate"] = {"path": gate.get_path_name(), "origin_cm": list(origin.to_tuple()),
                      "yaw_deg": math.degrees(yaw)}
    floor_z = 642.781
    capsule_z = floor_z + 96.0
    for lateral_cm in range(-4500, 4501, 500):
        outside = unreal.Vector(origin.x - forward.x * 5000 + side.x * lateral_cm,
                                origin.y - forward.y * 5000 + side.y * lateral_cm,
                                capsule_z)
        inside = unreal.Vector(origin.x + forward.x * 5000 + side.x * lateral_cm,
                               origin.y + forward.y * 5000 + side.y * lateral_cm,
                               capsule_z)
        hit = unreal.SystemLibrary.capsule_trace_single(
            world, outside, inside, 42.0, 96.0,
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
            unreal.DrawDebugTrace.NONE, True)
        outside_floor = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(outside.x, outside.y, floor_z + 300.0),
            unreal.Vector(outside.x, outside.y, floor_z - 200.0),
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
            unreal.DrawDebugTrace.NONE, True)
        inside_floor = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(inside.x, inside.y, floor_z + 300.0),
            unreal.Vector(inside.x, inside.y, floor_z - 200.0),
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
            unreal.DrawDebugTrace.NONE, True)
        report["sweeps"].append({
            "lateral_cm": lateral_cm,
            "outside_cm": list(outside.to_tuple()), "inside_cm": list(inside.to_tuple()),
            "clear_capsule": not bool(hit and hit.to_dict().get("blocking_hit")),
            "blocker": hit_data(hit),
            "outside_floor": hit_data(outside_floor),
            "inside_floor": hit_data(inside_floor),
        })
    report["success"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("HOSPITAL_GATE_CLEARANCE_PROBE " + json.dumps({
        "success": report["success"], "sweeps": len(report["sweeps"]),
        "clear_offsets_cm": [row["lateral_cm"] for row in report["sweeps"] if row["clear_capsule"]],
        "errors": report["errors"],
    }))
    unreal.SystemLibrary.quit_editor()
