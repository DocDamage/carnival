"""Verify BP_Swing_Carnival component counts by class."""
import unreal

SDFL = unreal.SubobjectDataBlueprintFunctionLibrary
BP_PATH = "/Game/Carnival/Rides/BP_Swing_Carnival"


def log(msg):
    unreal.log_warning("VERIFY: " + str(msg))


def main():
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    bp = unreal.load_asset(BP_PATH)
    if not bp:
        log("bp not found")
        return

    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    counts = {}
    for h in handles:
        obj = SDFL.get_associated_object(SDFL.get_data(h))
        if obj is None:
            continue
        cls = obj.get_class().get_name()
        counts[cls] = counts.get(cls, 0) + 1

    for cls in sorted(counts):
        if "Carnival" in cls or "Seat" in cls or "Ride" in cls:
            log("%s = %d" % (cls, counts[cls]))

    log("total subobjects: %d" % len(handles))

    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass


main()
