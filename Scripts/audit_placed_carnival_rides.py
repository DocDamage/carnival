"""Read-only per-instance inventory of rides in LV_Carnival and loaded lighting sublevels."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP_PATH = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REPORT_PATH = Path(r"F:\Carnival\Saved\RideDevelopment\Placed_Ride_Inventory.json")
RIDE_WORDS = (
    "ferris", "carousel", "swing", "pirate", "balloon", "teapot", "clown",
    "circus", "hauntedhouse", "bumper", "flyingbobs", "ride_", "ride-", "ride ",
)


def safe(fn):
    try:
        value = fn()
        if hasattr(value, "get_path_name"):
            return value.get_path_name()
        if hasattr(value, "to_tuple"):
            return [round(float(x), 2) for x in value.to_tuple()]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
    except Exception as exc:
        return "UNAVAILABLE: " + repr(exc)


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError(f"Could not load connected Carnival world {MAP_PATH}")

levels = list(unreal.EditorLevelUtils.get_levels(world))
all_actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

attendants = []
for actor in all_actors:
    class_name = actor.get_class().get_name()
    if "attendant" in class_name.lower() or "attendant" in actor.get_actor_label().lower():
        location = actor.get_actor_location()
        attendants.append({
            "label": actor.get_actor_label(),
            "class": class_name,
            "level": actor.get_level().get_path_name(),
            "location": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
            "path": actor.get_path_name(),
            "assigned_ride": safe(lambda a=actor: a.get_editor_property("ride")),
        })

queue_points = []
for actor in all_actors:
    if actor.get_class().get_name() != "CarnivalQueuePoint":
        continue
    location = actor.get_actor_location()
    queue_points.append({
        "label": actor.get_actor_label(),
        "ride_id": safe(lambda a=actor: a.get_editor_property("ride_id")),
        "queue_index": safe(lambda a=actor: a.get_editor_property("queue_index")),
        "level": actor.get_level().get_path_name(),
        "location": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
    })

rides = []
for actor in all_actors:
    class_name = actor.get_class().get_name()
    label = actor.get_actor_label()
    identity = (label + " " + class_name + " " + actor.get_path_name()).lower()
    if (not class_name.startswith("BP_") or class_name == "BP_PossessedDoll_C"
            or not any(word in class_name.lower() for word in RIDE_WORDS)):
        continue

    location = actor.get_actor_location()
    bounds_origin, bounds_extent = actor.get_actor_bounds(False)
    components = []
    operation_components = []
    controller_components = []
    seat_components = []
    queue_components = []
    for component in actor.get_components_by_class(unreal.ActorComponent):
        if not component:
            continue
        comp_class = component.get_class().get_name()
        entry = {"name": component.get_name(), "class": comp_class}
        if isinstance(component, unreal.SceneComponent):
            entry["relative_location"] = safe(lambda c=component: c.get_editor_property("relative_location"))
            entry["attach_parent"] = safe(lambda c=component: c.get_attach_parent())
        if "RideOperationComponent" in comp_class:
            operation_components.append(entry)
            entry["state"] = safe(lambda c=component: c.get_editor_property("state"))
            entry["attendant"] = safe(lambda c=component: c.get_editor_property("attendant"))
            entry["configuration_error"] = safe(lambda c=component: c.get_editor_property("configuration_error"))
        if "RideControllerComponent" in comp_class:
            controller_components.append(entry)
            entry["ride_id"] = safe(lambda c=component: c.get_editor_property("ride_id"))
        if "RideSeatComponent" in comp_class:
            seat_components.append(entry)
            entry["seat_id"] = safe(lambda c=component: c.get_editor_property("seat_id"))
        if "RideQueueComponent" in comp_class or "QueuePoint" in comp_class:
            queue_components.append(entry)
            entry["ride_id"] = safe(lambda c=component: c.get_editor_property("ride_id"))
        components.append(entry)

    ride_id = controller_components[0].get("ride_id") if controller_components else None
    if not ride_id or str(ride_id).startswith("UNAVAILABLE:"):
        class_lower = class_name.lower()
        inferred_ids = (
            ("ferriswheel", "FerrisWheel"), ("carousel", "Carousel"),
            ("bumper", "BumperCars"), ("flyingbobs", "FlyingBobs"),
        )
        ride_id = next((value for token, value in inferred_ids if token in class_lower), "")
    matching_queue_points = sum(1 for point in queue_points
                                if str(point["ride_id"]).lower() == str(ride_id).lower()) if ride_id else 0

    nearest = []
    for attendant in attendants:
        p = attendant["location"]
        d = math.sqrt((location.x - p[0]) ** 2 + (location.y - p[1]) ** 2 + (location.z - p[2]) ** 2)
        nearest.append({"label": attendant["label"], "distance_cm": round(d, 1), "level": attendant["level"]})
    nearest.sort(key=lambda row: row["distance_cm"])

    assigned_attendants = [staff["path"] for staff in attendants
                           if staff["assigned_ride"] == actor.get_path_name()]
    class_lower = class_name.lower()
    experience = ("walkthrough_or_show" if any(word in class_lower for word in ("hauntedhouse", "circus"))
                  else "driving_arena" if "bumper" in class_lower else "seated_cycle")
    blockers = []
    if not assigned_attendants:
        blockers.append("No attendant references this ride instance")
    if experience == "seated_cycle":
        if not controller_components:
            blockers.append("No passenger controller")
        if not seat_components:
            blockers.append("No authored passenger seats")
        seat_ids = [str(seat["seat_id"]) for seat in seat_components]
        if len(set(seat_ids)) != len(seat_ids) or any(value in ("", "None") for value in seat_ids):
            blockers.append("Passenger seat IDs are missing or duplicated")
    else:
        blockers.append("Requires separate " + experience + " acceptance; a seated-cycle result does not cover this attraction")

    rides.append({
        "label": label,
        "class": class_name,
        "path": actor.get_path_name(),
        "level": actor.get_level().get_path_name(),
        "location": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
        "bounds_origin": [round(bounds_origin.x, 2), round(bounds_origin.y, 2), round(bounds_origin.z, 2)],
        "bounds_extent": [round(bounds_extent.x, 2), round(bounds_extent.y, 2), round(bounds_extent.z, 2)],
        "ride_id": ride_id,
        "operation_component_count": len(operation_components),
        "controller_component_count": len(controller_components),
        "seat_component_count": len(seat_components),
        "queue_component_count": len(queue_components),
        "queue_points_for_ride_id": matching_queue_points,
        "operation_components": operation_components,
        "controller_components": controller_components,
        "seat_components": seat_components,
        "queue_components": queue_components,
        "nearest_attendants": nearest[:3],
        "assigned_attendants": assigned_attendants,
        "experience": experience,
        "authoring_blockers": blockers,
        "runtime_acceptance": "not_run",
        "components": components,
    })

rides.sort(key=lambda item: (item["level"], item["class"], item["label"]))
report = {
    "schema": 2,
    "map": MAP_PATH,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "saved_map_modified": False,
    "level_count": len(levels),
    "levels": [level.get_path_name() for level in levels],
	"loaded_levels": [level.get_path_name() for level in levels],
    "attendant_count": len(attendants),
    "attendants": attendants,
    "queue_point_count": len(queue_points),
    "queue_points": queue_points,
    "queue_point_counts_by_ride_id": {
        str(key): len([point for point in queue_points if str(point["ride_id"]) == str(key)])
        for key in sorted(set(str(point["ride_id"]) for point in queue_points))
    },
    "ride_instance_count": len(rides),
    "ride_instances": rides,
    "instances_with_authoring_blockers": sum(bool(ride["authoring_blockers"]) for ride in rides),
    "shared_queue_ids": {
        ride_id: [ride["path"] for ride in rides if ride["ride_id"] == ride_id]
        for ride_id in sorted(set(ride["ride_id"] for ride in rides if ride["ride_id"]))
        if sum(ride["ride_id"] == ride_id for ride in rides) > 1
    },
}
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("PLACED_CARNIVAL_RIDE_INVENTORY " + json.dumps({
    "levels": len(levels), "attendants": len(attendants), "ride_instances": len(rides),
    "report": str(REPORT_PATH),
}))
unreal.SystemLibrary.quit_editor()
