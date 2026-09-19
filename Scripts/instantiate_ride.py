"""Replace a base Creepwood ride actor with its CarnivalKit child Blueprint.

Finds the base ride actor by label/class substring, spawns the derived child
Blueprint at the exact same transform (location/rotation/scale), then destroys
the base actor (configurable). The derived Blueprint carries the Carnival
components (RideId, motion source, seats) from wire_ride.py.

Run headlessly:
    UnrealEditor.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="<this file>" -ExecCmds="quit"
"""
import unreal

MAP_PATH = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
BASE_SUBSTR = "Swing_Ride"
CHILD_BP_PATH = "/Game/Carnival/Rides/BP_Swing_Carnival"
DESTROY_ORIGINAL = True


def log(msg):
    unreal.log_warning("RIDE: " + str(msg))


def find_actor(substr):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors():
        if actor is None:
            continue
        label = actor.get_actor_label() or ""
        cls = actor.get_class().get_name() if actor.get_class() else ""
        if substr.lower() in label.lower() or substr.lower() in cls.lower():
            return actor
    return None


def main():
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    log("loaded map " + MAP_PATH)

    base = find_actor(BASE_SUBSTR)
    if base is None:
        log("base ride not found: " + BASE_SUBSTR)
        return
    log("found base: %s (%s)" % (base.get_actor_label(), base.get_class().get_name()))

    bp = unreal.load_asset(CHILD_BP_PATH)
    if bp is None:
        log("child Blueprint not found: " + CHILD_BP_PATH)
        return
    bp_class = bp.generated_class()
    log("child class: " + bp_class.get_name())

    location = base.get_actor_location()
    rotation = base.get_actor_rotation()
    scale = base.get_actor_scale3d()

    child = unreal.EditorLevelLibrary.spawn_actor_from_class(bp_class, location, rotation)
    if child is None:
        log("failed to spawn child Blueprint")
        return
    child.set_actor_scale3d(scale)
    child.set_actor_label("BP_Swing_Carnival")
    log("spawned child at %s rot %s scale %s" % (str(location), str(rotation), str(scale)))

    if DESTROY_ORIGINAL:
        destroyed = False
        try:
            unreal.EditorLevelLibrary.destroy_actor(base)
            destroyed = True
        except Exception as exc:
            log("EditorLevelLibrary.destroy_actor failed: %s" % exc)
        if not destroyed:
            try:
                base.destroy_actor()
                destroyed = True
            except Exception as exc:
                log("native destroy failed: %s" % exc)
        log("destroyed base: %s" % destroyed)

    saved = unreal.EditorLevelLibrary.save_current_level()
    log("save_current_level -> %s" % saved)
    log("done")


main()
