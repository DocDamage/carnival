"""Correct Rotator field order on the saved generated outer-route boxes."""
import json
import math
import re
import traceback
from pathlib import Path

import unreal

ROOT = Path(r"F:\Carnival")
PACKAGE = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout"
REGION_PATH = ROOT / "Saved/WorldExpansion/Region_Authoring.json"
OUT = ROOT / "Saved/WorldExpansion/Outer_Route_Rotation_Repair.json"


def catmull(controls, step=700.0):
    points = []
    for index in range(len(controls) - 1):
        p0, p1 = controls[max(index - 1, 0)], controls[index]
        p2, p3 = controls[index + 1], controls[min(index + 2, len(controls) - 1)]
        count = max(2, int(math.ceil(math.dist(p1, p2) / step)))
        for j in range(count):
            t = j / float(count)
            t2, t3 = t * t, t * t * t
            points.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t
                                  + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                  + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
                                for k in range(3)))
    points.append(tuple(controls[-1]))
    return points


report = {"success": False, "package": PACKAGE, "actors_changed": 0, "errors": []}
try:
    region = json.loads(REGION_PATH.read_text(encoding="utf-8"))
    controls = region["outer_route_spine"]["controls_cm"]
    points = catmull(controls)
    world = unreal.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    if not world:
        raise RuntimeError("Could not open the generated connector level")
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = [actor for actor in subsystem.get_all_level_actors()
              if actor.get_actor_label() == "OuterRoute_Segment"]
    if len(actors) != len(points) - 1 or len(actors) != 435:
        raise RuntimeError("Expected 435 generated route segments; found %d" % len(actors))

    def actor_index(actor):
        match = re.search(r"StaticMeshActor_(\d+)$", actor.get_path_name())
        if not match:
            raise RuntimeError("Unexpected outer-route actor path: " + actor.get_path_name())
        return int(match.group(1))

    actors.sort(key=actor_index)
    examples = []
    max_abs_pitch = 0.0
    for index, (actor, a, b) in enumerate(zip(actors, points, points[1:])):
        dx, dy, dz = (b[k] - a[k] for k in range(3))
        horizontal = max(1.0, math.hypot(dx, dy))
        pitch = math.degrees(math.atan2(dz, horizontal))
        yaw = math.degrees(math.atan2(dy, dx))
        before = actor.get_actor_rotation()
        actor.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), True)
        after = actor.get_actor_rotation()
        max_abs_pitch = max(max_abs_pitch, abs(after.pitch))
        if index in (0, 100, 218, 309, 400, 434):
            examples.append({"index": index, "actor": actor.get_path_name(),
                             "location_cm": list(actor.get_actor_location().to_tuple()),
                             "rotation_before": [before.pitch, before.yaw, before.roll],
                             "rotation_after": [after.pitch, after.yaw, after.roll],
                             "expected_rotation": [pitch, yaw, 0.0]})
        report["actors_changed"] += 1

    if max_abs_pitch > 5.0:
        raise RuntimeError("Corrected route contains an unexpectedly steep pitch: %.3f" % max_abs_pitch)
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, PACKAGE):
        raise RuntimeError("Could not save the corrected connector level")
    report.update({"success": True, "max_abs_pitch_degrees": max_abs_pitch,
                   "actor_count": len(actors), "backup": str(ROOT / "Saved/WorldExpansion/Backups/L_CarnivalWorldExpansion_Connections_Layout_before_rotation_repair_20260929.umap"),
                   "examples": examples,
                   "change": "Only the Pitch/Yaw/Roll assignment on the 435 OuterRoute_Segment actors was corrected."})
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("OUTER_ROUTE_ROTATION_REPAIR " + json.dumps({
        "success": report.get("success"), "actors_changed": report.get("actors_changed"),
        "max_abs_pitch_degrees": report.get("max_abs_pitch_degrees"), "errors": report["errors"]}))
    unreal.SystemLibrary.quit_editor()
