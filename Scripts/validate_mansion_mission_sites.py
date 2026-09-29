"""Probe local floor contacts and player capsule clearance at proposed mansion mission sites."""

import json
import math
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT = ROOT / "Saved/MansionConnection/Mission_Site_Clearance.json"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in actors}
landmarks = {
    "Coastal driveway end": (-69105.98, -84621.55, 598.0),
    "Mansion door leaf": (-69129.01, -85414.84, 612.90),
    "Foyer floor candidate": (-69895.73, -85984.76, 619.92),
    "Study table": (-70233.20, -88682.48, 817.94),
    "Music room table": (-71082.33, -89032.89, 817.34),
}
door = by_label.get("BP_Door7")
if door:
    p = door.get_actor_location()
    landmarks["Keyed music-room door"] = (p.x, p.y, p.z)


def tuple_hit(hit):
    return hit.to_tuple() if hit else None


def trace_floor(x, y, z):
    start = unreal.Vector(x, y, z + 130.0)
    end = unreal.Vector(x, y, z - 260.0)
    hit = tuple_hit(unreal.SystemLibrary.line_trace_single(
        world, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True
    ))
    if not hit or not hit[0]:
        return None
    point = hit[5]
    normal = hit[7]
    actor = hit[9]
    return {
        "z": point.z,
        "normal": list(normal.to_tuple()),
        "actor": actor.get_actor_label() if actor else None,
    }


def capsule_blocked(center, ignore):
    end = center + unreal.Vector(0.0, 0.0, 0.1)
    hit = tuple_hit(unreal.SystemLibrary.capsule_trace_single(
        world, center, end, 42.0, 96.0, unreal.TraceTypeQuery.ECC_VISIBILITY,
        False, ignore, unreal.DrawDebugTrace.NONE, True
    ))
    return bool(hit and hit[0]), (hit[9].get_actor_label() if hit and hit[0] and hit[9] else None)


report = {"map": MAP, "sites": [], "direct_segments": []}
for name, (x, y, z) in landmarks.items():
    floor = trace_floor(x, y, z)
    site = {"name": name, "landmark": [x, y, z], "floor": floor, "standing_options": []}
    if floor:
        for dx, dy in ((0, 180), (0, -180), (180, 0), (-180, 0), (130, 130), (-130, 130), (130, -130), (-130, -130)):
            sx, sy = x + dx, y + dy
            stand_floor = trace_floor(sx, sy, floor["z"])
            if not stand_floor:
                continue
            center = unreal.Vector(sx, sy, stand_floor["z"] + 97.0)
            blocked, blocker = capsule_blocked(center, [])
            sight = tuple_hit(unreal.SystemLibrary.line_trace_single(
                world,
                center + unreal.Vector(0, 0, 15),
                unreal.Vector(x, y, z + 30),
                unreal.TraceTypeQuery.ECC_VISIBILITY,
                False,
                [],
                unreal.DrawDebugTrace.NONE,
                True,
            ))
            sight_blocker = sight[9].get_actor_label() if sight and sight[0] and sight[9] else None
            site["standing_options"].append({
                "location": [sx, sy, center.z],
                "floor_z": stand_floor["z"],
                "walkable_normal_z": stand_floor["normal"][2],
                "blocked": blocked,
                "blocker": blocker,
                "interaction_sight_clear": not bool(sight and sight[0]),
                "sight_blocker": sight_blocker,
            })
    report["sites"].append(site)

for first, second in zip(report["sites"], report["sites"][1:]):
    first_options = [entry for entry in first["standing_options"] if not entry["blocked"]]
    second_options = [entry for entry in second["standing_options"] if not entry["blocked"]]
    if not first_options or not second_options:
        report["direct_segments"].append({"from": first["name"], "to": second["name"], "success": False, "reason": "No clear standing point"})
        continue
    a = unreal.Vector(*first_options[0]["location"])
    b = unreal.Vector(*second_options[0]["location"])
    hit = tuple_hit(unreal.SystemLibrary.capsule_trace_single(
        world, a, b, 42.0, 96.0, unreal.TraceTypeQuery.ECC_VISIBILITY,
        False, [], unreal.DrawDebugTrace.NONE, True
    ))
    report["direct_segments"].append({
        "from": first["name"],
        "to": second["name"],
        "success": not bool(hit and hit[0]),
        "blocker": hit[9].get_actor_label() if hit and hit[0] and hit[9] else None,
    })

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"MANSION_MISSION_SITE_CLEARANCE {REPORT}")
unreal.SystemLibrary.quit_editor()
