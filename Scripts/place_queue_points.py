"""Place CarnivalQueuePoint actors along a ride's queue in the loaded level.

Finds the ride actor by label/class substring, then places a straight line of
queue points extending from the ride's forward vector (configurable). Sets
RideId + QueueIndex so the ride's CarnivalRideQueueComponent discovers and sorts
them at BeginPlay. Idempotent: clears existing queue points for the ride first.

Run headlessly:
    UnrealEditor.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="<this file>" -ExecCmds="quit"
"""
import unreal

# --- config ---
MAP_PATH = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
RIDE_ID = "Swing"
RIDE_SUBSTR = "Swing"
QUEUE_COUNT = 8
QUEUE_SPACING = 120.0        # cm between consecutive points
QUEUE_START_OFFSET = 250.0   # cm from ride origin along forward
QUEUE_POINT_CLASS = "/Script/CarnivalPopulation.CarnivalQueuePoint"
# --- end config ---


def log(msg):
    unreal.log_warning("QUEUE: " + str(msg))


def find_ride_actor(substr):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors():
        if actor is None:
            continue
        label = actor.get_actor_label() or ""
        cls = actor.get_class().get_name() if actor.get_class() else ""
        if substr.lower() in label.lower() or substr.lower() in cls.lower():
            return actor
    return None


def remove_queue_points(ride_id):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = 0
    for actor in list(subsystem.get_all_level_actors()):
        if actor is None or actor.get_class() is None:
            continue
        if actor.get_class().get_name() != "CarnivalQueuePoint":
            continue
        try:
            if str(actor.get_editor_property("RideId")) == ride_id:
                unreal.EditorLevelLibrary.destroy_actor(actor)
                removed += 1
        except Exception:
            pass
    return removed


def main():
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    log("loaded map " + MAP_PATH)

    ride = find_ride_actor(RIDE_SUBSTR)
    if ride is None:
        log("ride not found for substring: " + RIDE_SUBSTR)
        return
    log("found ride: %s (%s)" % (ride.get_actor_label(), ride.get_class().get_name()))

    removed = remove_queue_points(RIDE_ID)
    log("removed %d existing queue points" % removed)

    cls = unreal.load_class(None, QUEUE_POINT_CLASS)
    if cls is None:
        log("failed to load queue point class: " + QUEUE_POINT_CLASS)
        return

    origin = ride.get_actor_location()
    fwd = ride.get_actor_forward_vector()

    for i in range(QUEUE_COUNT):
        offset = QUEUE_START_OFFSET + i * QUEUE_SPACING
        pos = origin + fwd * offset
        point = unreal.EditorLevelLibrary.spawn_actor_from_class(
            cls, pos, unreal.Rotator(0.0, 0.0, 0.0))
        if point is None:
            log("failed to spawn point %d" % i)
            continue
        point.set_editor_property("RideId", RIDE_ID)
        point.set_editor_property("QueueIndex", i)
        point.set_actor_label("CarnivalQueuePoint_%s_%02d" % (RIDE_ID, i))
        log("placed %d at (%.1f, %.1f, %.1f)" % (i, pos.x, pos.y, pos.z))

    saved = unreal.EditorLevelLibrary.save_current_level()
    log("save_current_level -> %s" % saved)
    log("done")


main()
