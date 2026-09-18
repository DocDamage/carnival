"""Wire a Creepwood ride Blueprint for CarnivalKit (reversible derived Blueprint).

Creates /Game/Carnival/Rides/<OutputName> as a child of the vendor ride Blueprint,
adds CarnivalRideControllerComponent / CarnivalRideMotionComponent / CarnivalRideQueueComponent,
then (for seat-based rides) adds one CarnivalRideSeatComponent per seat mesh.

Run headlessly:
    UnrealEditor.exe "CarnivalGame.uproject" -unattended -nullrhi -nosplash
        -ExecutePythonScript="<this file>" -ExecCmds="quit"
"""
import re

import unreal

SDFL = unreal.SubobjectDataBlueprintFunctionLibrary
RIDE_PATH = "/Game/Carnival/Rides"

COMPONENTS = [
    ("CarnivalRideController", "/Script/CarnivalPopulation.CarnivalRideControllerComponent"),
    ("CarnivalRideMotion", "/Script/CarnivalPopulation.CarnivalRideMotionComponent"),
    ("CarnivalRideQueue", "/Script/CarnivalPopulation.CarnivalRideQueueComponent"),
]
SEAT_CLASS_PATH = "/Script/CarnivalPopulation.CarnivalRideSeatComponent"
SEAT_CLASS_NAME = "CarnivalRideSeatComponent"

# One entry per ride. seat_mesh_pattern + seat_number_regex define how seats are found.
RIDES = {
    "Swing": {
        "output": "BP_Swing_Carnival",
        "parent": "/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/BP_Swing_Ride_01a",
        "seat_mesh_pattern": "SM_Swing_Chair",
        "seat_exclude": "Chain",
        "seat_number_regex": r"Chair(\d+)",
    },
    "PirateShip": {
        "output": "BP_PirateShip_Carnival",
        "parent": "/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/BP_PirateShip_Ride_01a",
        # Pirate Ship has row benches (not discrete chair meshes): seats are placed manually.
        "seat_mesh_pattern": None,
    },
}


def log(msg):
    unreal.log_warning("WIRE: " + str(msg))


def _obj(h):
    return SDFL.get_associated_object(SDFL.get_data(h))


def _find_actor_handle(sds, bp):
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        if SDFL.is_actor(SDFL.get_data(h)):
            return h
    return None


def _delete_all_seats(sds, bp, actor_handle):
    deleted = 0
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        obj = _obj(h)
        if obj is not None and obj.get_class().get_name() == SEAT_CLASS_NAME:
            try:
                r = sds.delete_subobject(actor_handle, h, bp)
                deleted += int(r) if r else 0
            except Exception:
                pass
    return deleted


def wire(ride_id):
    cfg = RIDES[ride_id]
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

    # Delete existing output asset (idempotent rebuild).
    bp_path = "%s/%s" % (RIDE_PATH, cfg["output"])
    if unreal.EditorAssetLibrary.does_asset_exist(bp_path):
        unreal.EditorAssetLibrary.delete_asset(bp_path)
        log("[%s] deleted existing %s" % (ride_id, cfg["output"]))

    # Derive child Blueprint.
    parent = unreal.load_asset(cfg["parent"])
    if not parent:
        log("[%s] parent not found" % ride_id)
        return False
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent.generated_class())
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        cfg["output"], RIDE_PATH, unreal.Blueprint, factory)
    if not bp:
        log("[%s] create_asset failed" % ride_id)
        return False

    actor_handle = _find_actor_handle(sds, bp)
    if actor_handle is None:
        log("[%s] no actor handle" % ride_id)
        return False

    # Add controller/motion/queue.
    for name, cls_path in COMPONENTS:
        cls = unreal.load_object(None, cls_path)
        nh, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(actor_handle, cls, bp))
        if nh is not None:
            sds.rename_subobject(handle=nh, new_name=unreal.Text(name))
            log("[%s] added %s" % (ride_id, name))
        else:
            log("[%s] add %s failed: %s" % (ride_id, name, fail))

    # Add seats (one per seat mesh, deduped by number).
    if cfg.get("seat_mesh_pattern"):
        seat_cls = unreal.load_object(None, SEAT_CLASS_PATH)
        chairs = {}
        for h in sds.k2_gather_subobject_data_for_blueprint(bp):
            obj = _obj(h)
            if obj is None:
                continue
            n = obj.get_name()
            if cfg["seat_mesh_pattern"] not in n:
                continue
            if cfg.get("seat_exclude") and cfg["seat_exclude"] in n:
                continue
            m = re.search(cfg["seat_number_regex"], n)
            if m and m.group(1) not in chairs:
                chairs[m.group(1)] = h

        added = 0
        for num in sorted(chairs, key=int):
            nh, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(chairs[num], seat_cls, bp))
            if nh is None:
                continue
            sds.rename_subobject(handle=nh, new_name=unreal.Text("Seat_" + num))
            comp = _obj(nh)
            if comp is not None and hasattr(comp, "set_editor_property"):
                try:
                    comp.set_editor_property("SeatId", "Seat" + num)
                except Exception:
                    pass
            added += 1
        log("[%s] added %d seats for %d chairs" % (ride_id, added, len(chairs)))
    else:
        log("[%s] no automatic seat layout (place seats manually)" % ride_id)

    unreal.EditorAssetLibrary.save_asset(bp_path)
    log("[%s] saved %s" % (ride_id, bp_path))
    return True


def main():
    ride_id = "Swing"  # change to "PirateShip" for components-only wiring
    wire(ride_id)
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass


main()
