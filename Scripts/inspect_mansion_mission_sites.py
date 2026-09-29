"""Inventory authored actors around the connected mansion for mission placement."""

import json
import math
from pathlib import Path

import unreal


MAP_PATH = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT_PATH = Path(r"F:\Carnival\Saved\MansionConnection\Mission_Site_Inventory.json")
MANSION_CENTER = unreal.Vector(-69966.34, -85850.28, 500.0)
SEARCH_RADIUS = 14000.0

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError(f"Could not load connected world {MAP_PATH}")

levels = unreal.EditorLevelUtils.get_levels(world)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
inventory = []
keywords = ("door", "foyer", "study", "music", "box", "glove", "key", "worker", "hall", "stair", "doll")

for actor in actor_subsystem.get_all_level_actors():
    location = actor.get_actor_location()
    delta = location - MANSION_CENTER
    distance = math.sqrt(delta.x * delta.x + delta.y * delta.y + delta.z * delta.z)
    if distance > SEARCH_RADIUS:
        continue

    label = actor.get_actor_label()
    class_name = actor.get_class().get_name()
    object_path = actor.get_path_name()
    bounds_origin, bounds_extent = actor.get_actor_bounds(False)
    static_meshes = []
    try:
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            if mesh:
                static_meshes.append(mesh.get_path_name())
    except Exception:
        pass

    inventory.append({
        "label": label,
        "class": class_name,
        "path": object_path,
        "location": [location.x, location.y, location.z],
        "distance_from_mansion_center": distance,
        "bounds_origin": [bounds_origin.x, bounds_origin.y, bounds_origin.z],
        "bounds_extent": [bounds_extent.x, bounds_extent.y, bounds_extent.z],
        "static_meshes": static_meshes[:4],
        "keyword_match": any(word in (label + " " + class_name + " " + object_path).lower() for word in keywords),
    })

inventory.sort(key=lambda item: item["distance_from_mansion_center"])
report = {
    "map": MAP_PATH,
    "mansion_center": [MANSION_CENTER.x, MANSION_CENTER.y, MANSION_CENTER.z],
    "levels": [level.get_path_name() for level in levels],
    "actor_count_in_radius": len(inventory),
    "actors": inventory,
}
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"MANSION_MISSION_SITE_INVENTORY {json.dumps({'levels': len(levels), 'actors': len(inventory), 'report': str(REPORT_PATH)})}")
unreal.SystemLibrary.quit_editor()
