"""Stage the abandoned entrance doors open in the copied hospital architecture."""
import datetime
import json
import shutil
import sys
import unreal

sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import ROOT, OUT, HOSPITAL_ARCH_LEVEL

source = ROOT / "Content/Carnival/World/Levels/L_IndustrialHospitalInteriorArchitecture.umap"
backup = OUT / "Backups" / ("HospitalArchitecture_before_open_entrance_" +
    datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".umap")
world = unreal.EditorLoadingAndSavingUtils.load_map(HOSPITAL_ARCH_LEVEL)
if not world:
    raise RuntimeError("Copied hospital architecture failed to load")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
changes = []
# Source mesh origins lie on the two hinges; both leaves swing toward local +Y.
for label, yaw in (("SM_Door_Plate_03a11", 0), ("SM_Door_Plate_03b14", 180)):
    matches = [a for a in actors if a.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError("Expected one entrance leaf: " + label)
    actor = matches[0]
    changes.append({"actor": actor, "label": label, "before": actor.get_actor_rotation().to_tuple(), "yaw": yaw})
shutil.copy2(source, backup)
for change in changes:
    actor = change.pop("actor")
    actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=change["yaw"],roll=0), False)
    change["after"] = actor.get_actor_rotation().to_tuple()
    change["collision"] = str(actor.static_mesh_component.get_collision_enabled())
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Entrance save failed")
(OUT / "Entrance_Opening.json").write_text(json.dumps({"success": True,
    "backup": str(backup), "changes": changes, "interactive": False}, indent=2))
