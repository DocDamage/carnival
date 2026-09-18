"""UE 5.8 Editor Python helper.
Scans the current level for likely Creepwood ride actors and writes a report.
Run from Unreal's Python console: exec(open(r'<path>/scan_creepwood_level.py').read())
"""
import json
import os
import unreal

KEYWORDS = {
    "FerrisWheel": ["ferris"],
    "BumperCars": ["bumper"],
    "Carousel": ["carousel"],
    "Circus": ["circus"],
    "ClownRide": ["clown"],
    "FlyingBob": ["flyingbob", "flying_bob", "flying bob"],
    "HauntedHouse": ["haunted"],
    "HotAirBalloon": ["hotair", "hot_air", "hot air", "balloon"],
    "PirateShip": ["pirate"],
    "Swing": ["swing"],
    "Teapot": ["teapot", "tea_pot", "tea pot"],
    "BalloonTower": ["tower", "balloon tower", "balloontower"],
}

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = subsys.get_all_level_actors()
results = []

for actor in actors:
    label = actor.get_actor_label()
    cls = actor.get_class().get_name()
    haystack = f"{label} {cls}".lower()
    matches = []
    for ride_id, words in KEYWORDS.items():
        matched = False
        for word in words:
            if word in haystack:
                matched = True
                break
        if matched:
            matches.append(ride_id)
    if not matches:
        continue

    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    results.append({
        "label": label,
        "class": cls,
        "object_path": actor.get_path_name(),
        "matches": matches,
        "transform": {
            "location": [loc.x, loc.y, loc.z],
            "rotation": [rot.roll, rot.pitch, rot.yaw],
            "scale": [scale.x, scale.y, scale.z],
        },
    })

out_dir = os.path.join(unreal.Paths.project_saved_dir(), "CarnivalKit")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "CreepwoodRideCandidates.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"candidate_count": len(results), "candidates": results}, f, indent=2)

unreal.log(f"CarnivalKit: wrote {len(results)} ride candidates to {out_path}")
for row in results:
    unreal.log(f"  {row['label']} -> {', '.join(row['matches'])} [{row['class']}]")
