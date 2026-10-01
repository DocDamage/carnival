"""Read-only: stream the vendor wreck sublevels into LV_Carnival in memory (never saved) and
measure how the wreck sits in the world: per-actor world bounds, terrain height above its
footprint, and overlap with the Shipwreck water volume."""
import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\ShipwreckSublevelFit_20261001.json")
MAIN_MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
REGION_OFFSET = (-6033.089, -10010.0, -2108.649)
SUBLEVELS = ["/Game/UnderwaterShip/Levels/Sublevels/" + n for n in ("Ship", "SetDressing_Interior", "SetDressing_Exterior")]
EDITOR_ONLY_BLOCKERS = ("SM_Landscape_Far_01a",)

report = {"success": False}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    t = unreal.Transform()
    t.set_editor_property("translation", unreal.Vector(*REGION_OFFSET))
    added = []
    for pkg in SUBLEVELS:
        s = unreal.EditorLevelUtils.add_level_to_world_with_transform(world, pkg, unreal.LevelStreamingAlwaysLoaded, t)
        added.append({"package": pkg, "ok": bool(s)})
    report["added_in_memory"] = added

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    wreck, water = [], []
    for a in actors:
        lv = a.get_level().get_outermost().get_name()
        if lv in SUBLEVELS:
            o, e = a.get_actor_bounds(True)
            wreck.append({"level": lv.split("/")[-1], "label": a.get_actor_label(), "class": a.get_class().get_name(),
                          "min": [round(v) for v in (o - e).to_tuple()], "max": [round(v) for v in (o + e).to_tuple()]})
        elif "Shipwreck" in lv or "Atlantis" in lv:
            c = a.get_class().get_name()
            if "Volume" in c:
                o, e = a.get_actor_bounds(False)
                water.append({"level": lv.split("/")[-1], "label": a.get_actor_label(), "class": c,
                              "min": [round(v) for v in (o - e).to_tuple()], "max": [round(v) for v in (o + e).to_tuple()]})
    report["wreck_actors"] = wreck
    report["region_volumes"] = water
    lo = [min(w["min"][i] for w in wreck) for i in range(3)]
    hi = [max(w["max"][i] for w in wreck) for i in range(3)]
    report["wreck_bounds"] = {"min": lo, "max": hi}

    # Highest surface above each grid point of the wreck footprint, ignoring the wreck itself.
    wreck_actors = [a for a in actors if a.get_level().get_outermost().get_name() in SUBLEVELS]
    grid = []
    for ix in range(9):
        for iy in range(5):
            x = lo[0] + (hi[0] - lo[0]) * ix / 8.0
            y = lo[1] + (hi[1] - lo[1]) * iy / 4.0
            hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(x, y, 30000), unreal.Vector(x, y, -6000),
                                                          unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, wreck_actors,
                                                          unreal.DrawDebugTrace.NONE, True) or []
            rows = []
            for h in hits:
                ht = h.to_tuple()
                actor = ht[9] if len(ht) > 9 else None
                name = actor.get_actor_label() if actor else "?"
                if any(k in name for k in EDITOR_ONLY_BLOCKERS):
                    continue
                rows.append({"z": round(ht[4].z), "actor": name,
                             "level": actor.get_level().get_outermost().get_name().split("/")[-1] if actor else "?"})
            grid.append({"x": round(x), "y": round(y), "hits": rows[:4]})
    report["overhead_surfaces"] = grid
    report["success"] = True
except Exception:
    report["error"] = traceback.format_exc()
OUT.write_text(json.dumps(report, indent=1))
print("SHIPWRECK_FIT_DONE", OUT)
