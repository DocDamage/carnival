"""Read-only: why the Shipwreck wreck is missing in play.

Reports the vendor showcase map's streaming levels (package, class, transform), what each
vendor sublevel contains (class counts, lights/sky/fog/post-process that would clash with
Carnival's lighting), its bounds, and how LV_Carnival currently streams the Shipwreck region.
"""
import collections
import json
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\ShipwreckSublevels_20261001.json")
VENDOR_MAP = "/Game/UnderwaterShip/Levels/UnderwaterShip_Showcase_Exterior"
REGION_MAP = "/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck"
MAIN_MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
LIGHTING = ("Light", "Sky", "Fog", "PostProcess", "Atmosphere", "Cloud", "Reflection", "LightmassImportance")


def tf(t):
    r = t.rotation.rotator()
    return {"loc": [round(v, 2) for v in t.translation.to_tuple()],
            "rot": {"roll": round(r.roll, 2), "pitch": round(r.pitch, 2), "yaw": round(r.yaw, 2)},
            "scale": [round(v, 3) for v in t.scale3d.to_tuple()]}


SUBLEVELS = ["/Game/UnderwaterShip/Levels/Sublevels/" + n for n in ("Ship", "SetDressing_Interior", "SetDressing_Exterior")]
CANDIDATES = SUBLEVELS + [REGION_MAP]


def streaming_of(world):
    rows = []
    for pkg in CANDIDATES:
        s = unreal.GameplayStatics.get_streaming_level(world, unreal.Name(pkg))
        if s:
            rows.append({"package": pkg, "class": s.get_class().get_name(),
                         "transform": tf(s.get_editor_property("level_transform"))})
    rows.append({"loaded_levels": [l.get_outermost().get_name() for l in unreal.EditorLevelUtils.get_levels(world)]})
    return rows


def contents(world):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    per = collections.defaultdict(lambda: {"classes": collections.Counter(), "lighting": [], "min": None, "max": None})
    for a in actors:
        lv = a.get_level().get_outermost().get_name()
        c = a.get_class().get_name()
        d = per[lv]
        d["classes"][c] += 1
        if any(k in c for k in LIGHTING):
            d["lighting"].append({"label": a.get_actor_label(), "class": c,
                                  "loc": [round(v) for v in a.get_actor_location().to_tuple()]})
        o, e = a.get_actor_bounds(True)
        if e.x > 1e5 or e.y > 1e5:
            continue
        lo, hi = (o - e).to_tuple(), (o + e).to_tuple()
        d["min"] = lo if d["min"] is None else tuple(min(x, y) for x, y in zip(d["min"], lo))
        d["max"] = hi if d["max"] is None else tuple(max(x, y) for x, y in zip(d["max"], hi))
    return {k: {"actors": sum(v["classes"].values()), "classes": dict(v["classes"].most_common(20)),
                "lighting": v["lighting"],
                "bounds_min": [round(x) for x in v["min"]] if v["min"] else None,
                "bounds_max": [round(x) for x in v["max"]] if v["max"] else None}
            for k, v in per.items()}


report = {}
try:
    for key, path in (("vendor", VENDOR_MAP), ("region", REGION_MAP), ("main", MAIN_MAP)):
        w = unreal.EditorLoadingAndSavingUtils.load_map(path)
        entry = {"map": path, "streaming": streaming_of(w)}
        if key != "main":
            entry["contents"] = contents(w)
        else:
            entry["streaming"] = entry["streaming"][:-1]
        report[key] = entry
    report["success"] = True
except Exception as ex:
    import traceback
    report["success"] = False
    report["error"] = traceback.format_exc()
OUT.write_text(json.dumps(report, indent=1))
print("SHIPWRECK_INSPECT_DONE", OUT)
