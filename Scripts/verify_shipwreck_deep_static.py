"""Read-only check of the sunk Shipwreck in LV_Carnival: wreck pieces stay under the cavern ceiling and above
its floor, the shaft drops onto the wreck, and the ceiling is closed everywhere else."""
import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\ShipwreckDeep_20261001\static_check.json")
MAIN_MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
WRECK_LEVELS = ("L_CarnivalWorldExpansion_ShipwreckHull", "L_CarnivalWorldExpansion_ShipwreckDressingInterior",
                "L_CarnivalWorldExpansion_ShipwreckDressingExterior", "L_CarnivalWorldExpansion_Shipwreck")
CEIL_BOTTOM, FLOOR_TOP = -1990.0, -5200.0
R = {"success": False, "errors": [], "wreck": [], "over_ceiling": [], "under_floor": [], "shaft_drops": [], "closed_ceiling": []}


def first_hit(world, x, y, z_from, z_to):
    hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(x, y, z_from), unreal.Vector(x, y, z_to),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
                                                 unreal.DrawDebugTrace.NONE, True) or []
    for h in hits:
        t = h.to_tuple()
        a = t[9]
        if a and "SM_Landscape_Far_01a" in a.get_actor_label():
            continue
        return {"z": round(t[4].z), "actor": a.get_actor_label() if a else "?",
                "level": a.get_level().get_outermost().get_name().rsplit("/", 1)[1] if a else "?"}
    return None


try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lv = a.get_level().get_outermost().get_name().rsplit("/", 1)[1]
        if lv not in WRECK_LEVELS:
            continue
        o, e = a.get_actor_bounds(True)
        lo, hi = o - e, o + e
        if e.z == 0 and e.x == 0:
            continue
        row = {"level": lv, "label": a.get_actor_label(), "min_z": round(lo.z), "max_z": round(hi.z)}
        R["wreck"].append(row)
        if hi.z > CEIL_BOTTOM:
            R["over_ceiling"].append(row)
        if lo.z < FLOOR_TOP - 150:
            R["under_floor"].append(row)
    for x in (-6900, -6400, -5900):
        for y in (-11100, -10400, -9700):
            R["shaft_drops"].append({"x": x, "y": y, "hit": first_hit(world, x, y, -1700, -5600)})
    for x, y in ((-9500, -10000), (-4500, -10000), (-6400, -12000), (-6400, -8500), (-3500, -7000)):
        R["closed_ceiling"].append({"x": x, "y": y, "hit": first_hit(world, x, y, -1700, -5600)})
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
OUT.write_text(json.dumps(R, indent=1))
print("SHIPWRECK_STATIC_DONE")
