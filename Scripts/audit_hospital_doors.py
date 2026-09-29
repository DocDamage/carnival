"""Inspect copied hospital doors and capsule clearance without saving changes."""
import json
import math
import sys
import traceback
from pathlib import Path
import unreal

sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import MAIN_MAP, OUT, HOSPITAL_YAW, hospital_level_transform, world_point as route_world

report = {"success": False, "errors": [], "doors": [], "entrance_sweeps": []}
angle = math.radians(HOSPITAL_YAW)
origin = hospital_level_transform()

def world_point(p):
    x, y, z = p
    return unreal.Vector(origin[0] + x*math.cos(angle)-y*math.sin(angle),
                         origin[1] + x*math.sin(angle)+y*math.cos(angle), origin[2]+z)

def trace(a, b):
    hit = unreal.SystemLibrary.capsule_trace_single(world, world_point(a), world_point(b),
        42, 96, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True)
    h = hit.to_tuple() if hit else None
    if not h or not h[0]:
        return None
    return {"actor": h[9].get_actor_label() if h[9] else None,
            "actor_path": h[9].get_path_name() if h[9] else None,
            "point": h[5].to_tuple(), "normal": h[7].to_tuple()}

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    if not world:
        raise RuntimeError("Connected map failed to load")
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if "IndustrialHospitalInteriorArchitecture" not in actor.get_level().get_path_name():
            continue
        if "door" not in actor.get_actor_label().lower() and "door" not in actor.get_class().get_name().lower():
            continue
        record = {"label": actor.get_actor_label(), "class": actor.get_class().get_name(),
                  "path": actor.get_path_name(), "location": actor.get_actor_location().to_tuple(),
                  "door_api": [name for name in dir(actor) if any(word in name.lower()
                      for word in ("open", "close", "interact", "angle", "locked"))], "components": []}
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            transform = component.get_world_transform()
            record["components"].append({"name": component.get_name(),
                "mesh": mesh.get_path_name() if mesh else None,
                "location": transform.translation.to_tuple(),
                "rotation": transform.rotation.rotator().to_tuple(),
                "collision": str(component.get_collision_enabled()),
                "profile": str(component.get_collision_profile_name())})
        report["doors"].append(record)
    # Source doorway center is x=5200, wall y=-1775, floor z=80.
    # Trace from the forecourt into the entry corridor at player capsule height.
    for x in (5100, 5150, 5200, 5250, 5300):
        a, b = (x, -2300, 199), (x, -1400, 199)
        report["entrance_sweeps"].append({"start_local": a, "end_local": b, "hit": trace(a, b)})
    report["forecourt_floor"] = []
    for s in range(149800, 151201, 200):
        for lateral in range(-1200, 1201, 400):
            p = unreal.Vector(*route_world((s, lateral, 600)))
            hit = unreal.SystemLibrary.line_trace_single(world, p+unreal.Vector(0,0,100),
                p-unreal.Vector(0,0,1200), unreal.TraceTypeQuery.ECC_VISIBILITY,
                False, [], unreal.DrawDebugTrace.NONE, True)
            h = hit.to_tuple() if hit else None
            report["forecourt_floor"].append({"route_local": [s,lateral,600],
                "actor": h[9].get_actor_label() if h and h[0] and h[9] else None,
                "height_difference": h[5].z-p.z if h and h[0] else None})
    report["success"] = True
    runtime_path = OUT / "Hospital_Entrance_Playtest.json"
    if runtime_path.exists():
        runtime = json.loads(runtime_path.read_text())
        if runtime.get("stuck_location"):
            x,y,z = [a-b for a,b in zip(runtime["stuck_location"], origin)]
            local = (x*math.cos(angle)+y*math.sin(angle), -x*math.sin(angle)+y*math.cos(angle), z)
            report["runtime_stuck"] = {"local":local,
                "hit":trace(local,(local[0],local[1]+250,local[2]))}
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    (OUT / "Hospital_Door_Audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("HOSPITAL_DOOR_AUDIT " + str(report["success"]))
