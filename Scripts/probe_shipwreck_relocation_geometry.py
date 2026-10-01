"""Read-only: world-space geometry of everything tied to the Shipwreck's position, to plan
sinking the region: Shipwreck/Atlantis region actors, R12 tunnel pieces, flood volumes and
campaign stations near the wreck."""
import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\ShipwreckRelocationGeometry_20261001.json")
MAIN_MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"


def box(a):
    o, e = a.get_actor_bounds(False)
    return {"min": [round(v) for v in (o - e).to_tuple()], "max": [round(v) for v in (o + e).to_tuple()]}


report = {"success": False, "shipwreck": [], "atlantis_summary": None, "atlantis_east": [], "r12": [], "volumes": [], "stations": []}
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    at_lo, at_hi = [1e9] * 3, [-1e9] * 3
    for a in actors:
        lv = a.get_level().get_outermost().get_name().split("/")[-1]
        label = a.get_actor_label()
        c = a.get_class().get_name()
        b = box(a)
        if max(b["max"][i] - b["min"][i] for i in range(2)) > 60000:
            continue
        row = {"level": lv, "label": label, "class": c, **b}
        if lv == "L_CarnivalWorldExpansion_Shipwreck":
            report["shipwreck"].append(row)
        elif lv == "L_CarnivalWorldExpansion_Atlantis":
            for i in range(3):
                at_lo[i] = min(at_lo[i], b["min"][i]); at_hi[i] = max(at_hi[i], b["max"][i])
            if b["max"][0] > -10000:
                report["atlantis_east"].append(row)
        elif "AtlantisToShipwreck" in label or "R12" in label or "AtlantisHall" in label:
            report["r12"].append(row)
        if "Volume" in c and ("Flood" in label or "Water" in label):
            report["volumes"].append(row)
        if "Mission" in c or "Station" in c or "Campaign" in c:
            if b["max"][2] < 0:
                report["stations"].append(row)
    report["atlantis_summary"] = {"min": at_lo, "max": at_hi}
    report["success"] = True
except Exception:
    report["error"] = traceback.format_exc()
OUT.write_text(json.dumps(report, indent=1))
print("RELOCATION_GEOMETRY_DONE", OUT)
