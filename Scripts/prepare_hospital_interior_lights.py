"""Extract hospital interior lights, omitting the vendor's directional daylight."""
import hashlib
import json
import sys
import traceback
from pathlib import Path
import unreal
sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import HOSPITAL_LIGHT_LEVEL

ROOT = Path(r"F:\Carnival")
SOURCE = "/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_Light"
SOURCE_FILE = ROOT / "Content/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_Light.umap"
DEST_FILE = ROOT / "Content/Carnival/World/Levels/L_IndustrialHospitalInteriorLights.umap"
OUT = ROOT / "Saved/IndustrialHospital/Hospital_Lights_Copy.json"


def extract():
    if DEST_FILE.exists():
        raise FileExistsError("Refusing to overwrite the authored hospital light level")
    source_hash = hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest()
    world = unreal.EditorLoadingAndSavingUtils.load_map(SOURCE)
    if not world:
        raise RuntimeError("Could not load vendor hospital light source")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = list(eas.get_all_level_actors())
    selected = [a for a in all_actors if a.get_class().get_name() != "DirectionalLight"]
    removed_classes = {}
    for actor in all_actors:
        if actor.get_class().get_name() == "DirectionalLight":
            removed_classes[actor.get_class().get_name()] = removed_classes.get(actor.get_class().get_name(), 0) + 1
    if not selected:
        raise RuntimeError("No interior light actors were selected")
    streaming = unreal.EditorLevelUtils.create_new_streaming_level(
        unreal.LevelStreamingAlwaysLoaded, HOSPITAL_LIGHT_LEVEL, False
    )
    if not streaming:
        raise RuntimeError("Could not create a local hospital light sublevel")
    streaming.set_editor_property("should_be_loaded", True)
    streaming.set_editor_property("should_be_visible", True)
    typed = unreal.Array.cast(unreal.Actor, selected)
    moved = unreal.EditorLevelUtils.move_actors_to_level(typed, streaming, False, False)
    if moved != len(selected):
        raise RuntimeError(f"Moved {moved} of {len(selected)} selected hospital lights")
    unreal.EditorLevelUtils.make_level_current(streaming)
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Could not save the local hospital light level")
    source_hash_after = hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest()
    if source_hash_after != source_hash:
        raise RuntimeError("The vendor hospital light source changed on disk")
    return {
        "phase": "complete",
        "source": SOURCE,
        "copy": HOSPITAL_LIGHT_LEVEL,
        "source_actors": len(all_actors),
        "interior_light_actors_moved": moved,
        "excluded_classes": removed_classes,
        "source_sha256_unchanged": True,
        "copy_bytes": DEST_FILE.stat().st_size if DEST_FILE.exists() else None,
    }


try:
    report = extract()
except Exception as exc:
    report = {"phase": "failed", "source": SOURCE, "copy": HOSPITAL_LIGHT_LEVEL, "error": repr(exc), "traceback": traceback.format_exc()}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("HOSPITAL_LIGHT_COPY_" + report["phase"].upper())
unreal.SystemLibrary.quit_editor()
