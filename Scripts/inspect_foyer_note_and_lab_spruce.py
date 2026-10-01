"""Read-only: the saved foyer clue note's rotation (B10) and every foliage instance intruding into the Lab A
interior (B9). Lab A interior = the bounding box of its floor pieces, shrunk 50 cm."""
import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\FoyerNoteAndLabSpruce_20261001.json")
R = {"success": False, "errors": []}
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for a in acts:
        if "Foyer" in a.get_actor_label() and "Note" in a.get_actor_label():
            r = a.get_actor_rotation()
            R.setdefault("notes", []).append({"label": a.get_actor_label(), "level": a.get_outermost().get_name(),
                                             "roll": round(r.roll, 2), "pitch": round(r.pitch, 2), "yaw": round(r.yaw, 2),
                                             "loc": [round(v) for v in a.get_actor_location().to_tuple()]})
    lab = [a for a in acts if a.get_outermost().get_name().endswith("L_CarnivalWorldExpansion_LabA")]
    floors = [a for a in lab if "floor" in a.get_actor_label().lower() and a.get_class().get_name() == "StaticMeshActor"]
    lo = [1e9] * 3; hi = [-1e9] * 3
    for f in floors:
        o, e = f.get_actor_bounds(False)
        for i, v in enumerate((o - e).to_tuple()): lo[i] = min(lo[i], v)
        for i, v in enumerate((o + e).to_tuple()): hi[i] = max(hi[i], v)
    R["lab_a_floor_box"] = {"min": [round(v) for v in lo], "max": [round(v) for v in hi], "floor_pieces": len(floors)}
    R["intruding_foliage"] = []
    for ifa in [a for a in acts if a.get_class().get_name() == "InstancedFoliageActor"]:
        for comp in ifa.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = comp.static_mesh.get_name() if comp.static_mesh else "?"
            for i in range(comp.get_instance_count()):
                t = comp.get_instance_transform(i, True)
                p = t.translation
                if lo[0] + 50 < p.x < hi[0] - 50 and lo[1] + 50 < p.y < hi[1] - 50 and lo[2] - 200 < p.z < hi[2] + 800:
                    R["intruding_foliage"].append({"foliage_actor": ifa.get_actor_label(), "level": ifa.get_outermost().get_name(),
                                                   "component": comp.get_name(), "mesh": mesh, "index": i,
                                                   "loc": [round(v) for v in p.to_tuple()]})
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
OUT.write_text(json.dumps(R, indent=1))
print("FOYER_SPRUCE_DONE")
