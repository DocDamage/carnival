"""Probe alternative mansion entrance and foyer anchors without saving the map."""

import json
import math
from pathlib import Path

import unreal


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT = ROOT / "Saved/MansionConnection/Mission_Entrance_Candidate_Clearance.json"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in actors}


def actor_point(label, z_override=None):
    actor = by_label.get(label)
    if not actor:
        raise RuntimeError(f"Missing landmark actor: {label}")
    p = actor.get_actor_location()
    return (p.x, p.y, z_override if z_override is not None else p.z)


landmarks = {
    "Mansion front door": actor_point("SM_Door02_E2"),
    "Outer stair 10 landing": (-69514.07, -85883.11, 719.35),
    "External floor 38": actor_point("SM_ExternalFloor38", 726.12),
    "Interior threshold static door": actor_point("SM_Door02_E", 821.75),
    "Door 12 threshold": actor_point("SM_Door12", 819.74),
    "Foyer inner floor 92": (-70225.17, -86766.43, 770.55),
    "Foyer inner floor 93": (-70770.50, -86384.58, 770.55),
    "Foyer inner floor 91": (-69922.40, -87154.12, 770.55),
    "Foyer inner floor 98": (-71366.98, -85970.88, 770.27),
    "Study table": (-70233.20, -88682.48, 817.94),
    "Music room table": (-71082.33, -89032.89, 817.34),
}


def hit_tuple(hit):
    return hit.to_tuple() if hit else None


def trace_floor(x, y, z):
    hit = hit_tuple(unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, z + 160.0),
        unreal.Vector(x, y, z - 280.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    if not hit or not hit[0]:
        return None
    point, normal, actor = hit[5], hit[7], hit[9]
    return {
        "z": point.z,
        "normal": list(normal.to_tuple()),
        "actor": actor.get_actor_label() if actor else None,
    }


def capsule_blocked(center):
    hit = hit_tuple(unreal.SystemLibrary.capsule_trace_single(
        world,
        center,
        center + unreal.Vector(0.0, 0.0, 0.1),
        42.0,
        96.0,
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
    ))
    return bool(hit and hit[0]), (hit[9].get_actor_label() if hit and hit[0] and hit[9] else None)


report = {"map": MAP, "sites": []}
offsets = []
for radius in (120.0, 180.0, 260.0, 360.0):
    offsets.extend((dx, dy) for dx, dy in (
        (0.0, radius), (0.0, -radius), (radius, 0.0), (-radius, 0.0),
        (radius, radius), (radius, -radius), (-radius, radius), (-radius, -radius),
    ))

for name, (x, y, z) in landmarks.items():
    floor = trace_floor(x, y, z)
    site = {"name": name, "landmark": [x, y, z], "floor": floor, "standing_options": []}
    if floor:
        for dx, dy in offsets:
            sx, sy = x + dx, y + dy
            stand_floor = trace_floor(sx, sy, floor["z"])
            if not stand_floor:
                continue
            center = unreal.Vector(sx, sy, stand_floor["z"] + 97.0)
            blocked, blocker = capsule_blocked(center)
            sight = hit_tuple(unreal.SystemLibrary.line_trace_single(
                world,
                center + unreal.Vector(0.0, 0.0, 15.0),
                unreal.Vector(x, y, z + 30.0),
                unreal.TraceTypeQuery.ECC_VISIBILITY,
                False,
                [],
                unreal.DrawDebugTrace.NONE,
                True,
            ))
            site["standing_options"].append({
                "offset": [dx, dy],
                "location": [sx, sy, center.z],
                "floor_z": stand_floor["z"],
                "floor_actor": stand_floor["actor"],
                "walkable_normal_z": stand_floor["normal"][2],
                "blocked": blocked,
                "blocker": blocker,
                "interaction_sight_clear": not bool(sight and sight[0]),
                "sight_blocker": sight[9].get_actor_label() if sight and sight[0] and sight[9] else None,
            })
    report["sites"].append(site)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"MANSION_ENTRANCE_CANDIDATE_CLEARANCE {REPORT}")
unreal.SystemLibrary.quit_editor()
