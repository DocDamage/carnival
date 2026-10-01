"""Read-only: open each Carnival lighting level (Day, Night, NightSnow) on its own and list foliage instances
whose base lies inside Lab A's floor footprint (world box from inspect_foyer_note_and_lab_spruce.py, shrunk 50 cm),
up to 8 m above its floor. Records component, instance index and mesh so a removal script can target them."""
import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\LabASpruce_LightingLevels_20261001.json")
BOX = ((-43419 + 50, -8191 + 50, -500), (-40514 - 50, -5059 - 50, 1450))  # trees root below the lab floor
MAPS = ["/Game/Creepwood_Carnival_Meshingun/Environment/Map/Lv_Lighting" + n for n in ("Day", "Night", "NightSnow")]
R = {"success": False, "errors": [], "levels": {}}
try:
    for m in MAPS:
        unreal.EditorLoadingAndSavingUtils.load_map(m)
        hits, total = [], 0
        for ifa in [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
                    if a.get_class().get_name() == "InstancedFoliageActor"]:
            for comp in ifa.get_components_by_class(unreal.InstancedStaticMeshComponent):
                n = comp.get_instance_count(); total += n
                if n > 3868:
                    t = comp.get_instance_transform(3868, True).translation
                    R.setdefault("instance_3868", []).append({"level": m.rsplit("/", 1)[1], "component": comp.get_name(),
                        "mesh": comp.static_mesh.get_name() if comp.static_mesh else "?", "loc": [round(v) for v in t.to_tuple()]})
                for i in range(n):
                    p = comp.get_instance_transform(i, True).translation
                    if all(BOX[0][k] < v < BOX[1][k] for k, v in enumerate(p.to_tuple())):
                        hits.append({"component": comp.get_name(), "mesh": comp.static_mesh.get_name() if comp.static_mesh else "?",
                                     "index": i, "loc": [round(v) for v in p.to_tuple()]})
        R["levels"][m.rsplit("/", 1)[1]] = {"instances_total": total, "inside_lab_a": hits}
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
OUT.write_text(json.dumps(R, indent=1))
print("LAB_SPRUCE_DONE")
