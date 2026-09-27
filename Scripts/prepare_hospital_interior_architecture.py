"""Make a local hospital architecture copy without its global skylight actor."""
import json
import sys
import traceback
from pathlib import Path
import unreal
sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import HOSPITAL_ARCH_LEVEL

ROOT = Path(r"F:\Carnival")
SOURCE = "/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_Architecture"
OUT = ROOT / "Saved/IndustrialHospital/Hospital_Architecture_Copy.json"


def prepare():
    report = {"source": SOURCE, "copy": HOSPITAL_ARCH_LEVEL}
    if not unreal.EditorAssetLibrary.does_asset_exist(HOSPITAL_ARCH_LEVEL):
        duplicate = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, HOSPITAL_ARCH_LEVEL)
        if not duplicate:
            raise RuntimeError("Hospital architecture map duplication failed")
        if not unreal.EditorAssetLibrary.save_loaded_asset(duplicate, False):
            raise RuntimeError("Could not save duplicated hospital architecture map")
    world = unreal.EditorLoadingAndSavingUtils.load_map(HOSPITAL_ARCH_LEVEL)
    if not world:
        raise RuntimeError("Could not load duplicated hospital architecture map")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = 0
    for actor in list(eas.get_all_level_actors()):
        if actor.get_class().get_name() == "BP_Skylight_01a_C":
            if not eas.destroy_actor(actor):
                raise RuntimeError("Could not remove source global skylight from local architecture copy")
            removed += 1
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Could not save local hospital architecture copy")
    report.update({"removed_skylight_actors": removed, "phase": "complete"})
    return report


try:
    report = prepare()
except Exception as exc:
    report = {"source": SOURCE, "copy": HOSPITAL_ARCH_LEVEL, "phase": "failed", "error": repr(exc), "traceback": traceback.format_exc()}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("HOSPITAL_ARCHITECTURE_COPY_" + report["phase"].upper())
unreal.SystemLibrary.quit_editor()
