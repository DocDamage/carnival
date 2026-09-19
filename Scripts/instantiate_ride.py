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
RIDES = [
    # (base actor substring, child Blueprint path)
    ("Swing_Ride", "/Game/Carnival/Rides/BP_Swing_Carnival"),
    ("PirateShip_Ride", "/Game/Carnival/Rides/BP_PirateShip_Carnival"),
    ("BalloonTower_Ride", "/Game/Carnival/Rides/BP_BalloonTower_Carnival"),
    ("Clown_Ride", "/Game/Carnival/Rides/BP_ClownRide_Carnival"),
    ("FlyingBobs_Ride", "/Game/Carnival/Rides/BP_FlyingBobs_Carnival"),
    ("Circus_Ride", "/Game/Carnival/Rides/BP_Circus_Carnival"),
    ("HauntedHouse_Ride", "/Game/Carnival/Rides/BP_HauntedHouse_Carnival"),
    ("HotairBalloon_Ride", "/Game/Carnival/Rides/BP_HotAirBalloon_Carnival"),
    ("Teapot_Ride_01a_SunshineShimmer", "/Game/Carnival/Rides/BP_Teapot_Carnival"),
]
DESTROY_ORIGINAL = True


def log(msg):
    unreal.log_warning("RIDE: " + str(msg))


def find_actors(substr):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    result = []
    for actor in subsystem.get_all_level_actors():
        if actor is None:
            continue
        label = actor.get_actor_label() or ""
        cls = actor.get_class().get_name() if actor.get_class() else ""
        if substr.lower() in label.lower() or substr.lower() in cls.lower():
            result.append(actor)
    return result


def main():
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    log("loaded map " + MAP_PATH)

    for base_substr, child_bp_path in RIDES:
        bp = unreal.load_asset(child_bp_path)
        if bp is None:
            log("child Blueprint not found: " + child_bp_path)
            continue
        bp_class = bp.generated_class()

        bases = find_actors(base_substr)
        if not bases:
            log("no base actors for: " + base_substr)
            continue

        log("=== %s: %d base actor(s) ===" % (base_substr, len(bases)))
        for idx, base in enumerate(bases):
            location = base.get_actor_location()
            rotation = base.get_actor_rotation()
            scale = base.get_actor_scale3d()

            child = unreal.EditorLevelLibrary.spawn_actor_from_class(bp_class, location, rotation)
            if child is None:
                log("failed to spawn child for %s" % base.get_actor_label())
                continue
            child.set_actor_scale3d(scale)

            class_name = bp_class.get_name()
            label = class_name[:-2] if class_name.endswith("_C") else class_name
            if len(bases) > 1:
                label = "%s_%d" % (label, idx)
            child.set_actor_label(label)
            log("replaced %s -> %s" % (base.get_actor_label(), label))

            if DESTROY_ORIGINAL:
                try:
                    unreal.EditorLevelLibrary.destroy_actor(base)
                except Exception as exc:
                    log("destroy failed for %s: %s" % (base.get_actor_label(), exc))

    saved = unreal.EditorLevelLibrary.save_current_level()
    log("save_current_level -> %s" % saved)
    log("done")


main()
