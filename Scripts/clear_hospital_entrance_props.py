"""Preserve source dressing; move three entrance tables in a connected local copy."""
import datetime
import hashlib
import json
import shutil
import sys
import gc
import unreal

sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import ROOT, OUT, MAIN_MAP, HOSPITAL_YAW, hospital_level_transform

source = "/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_SetDress"
target = "/Game/Carnival/World/Levels/L_IndustrialHospitalSetDress"
def file_for(asset):
    return ROOT / ("Content/" + asset.removeprefix("/Game/") + ".umap")
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
source_hash = digest(file_for(source))
backups = []
for asset in (MAIN_MAP, target):
    path = file_for(asset)
    if path.exists():
        backup = OUT / "Backups" / (path.stem + "_before_entry_props_" + stamp + ".umap")
        shutil.copy2(path, backup)
        backups.append(str(backup))
if not unreal.EditorAssetLibrary.does_asset_exist(target):
    copy = unreal.EditorAssetLibrary.duplicate_asset(source, target)
    if not copy or not unreal.EditorAssetLibrary.save_loaded_asset(copy, False):
        raise RuntimeError("Could not create local set-dressing copy")
    del copy
    gc.collect()
    unreal.SystemLibrary.collect_garbage()
world = unreal.EditorLoadingAndSavingUtils.load_map(target)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
# Preserve the three-table arrangement, shifting it onto the paved forecourt
# beside the entrance. Absolute positions make repeated runs idempotent.
positions = {
    "SM_TreatmentTable_04a": (6012.095703125, -2569.433349609375, 80),
    "SM_TreatmentTable_03a3": (6119.5576171875, -2473.91455078125, 80),
    "SM_TreatmentTable_01a": (6074.990234375, -2506.024658203125, 108),
}
changes = []
for label, position in positions.items():
    matches = [a for a in actors if a.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError("Expected one table: " + label)
    actor = matches[0]
    changes.append({"label": label, "before": actor.get_actor_location().to_tuple(), "after": position})
    actor.set_actor_location(unreal.Vector(*position), False, True)
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save copied dressing")
del actor, matches, actors, world
gc.collect()
world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
for level in list(unreal.EditorLevelUtils.get_levels(world)):
    path = level.get_path_name().split(":PersistentLevel")[0].split(".")[0]
    if path in (source, target):
        if not unreal.EditorLevelUtils.remove_level_from_world(level):
            raise RuntimeError("Could not replace dressing stream")
transform = unreal.Transform()
transform.translation = unreal.Vector(*hospital_level_transform())
transform.rotation = unreal.Rotator(pitch=0,yaw=HOSPITAL_YAW,roll=0).quaternion()
transform.scale3d = unreal.Vector(1,1,1)
stream = unreal.EditorLevelUtils.add_level_to_world_with_transform(world, target,
    unreal.LevelStreamingAlwaysLoaded, transform)
if not stream:
    raise RuntimeError("Could not connect local dressing")
stream.set_editor_property("should_be_loaded", True)
stream.set_editor_property("should_be_visible", True)
if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAIN_MAP):
    raise RuntimeError("Could not save root streaming reference")
if digest(file_for(source)) != source_hash:
    raise RuntimeError("Source dressing unexpectedly changed")
(OUT / "Entrance_Props_Correction.json").write_text(json.dumps({"success":True,
    "source_unchanged_sha256":source_hash,"copy":target,"backups":backups,"changes":changes},indent=2))
