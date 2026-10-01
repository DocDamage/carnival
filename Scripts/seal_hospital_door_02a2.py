"""Seal hospital double door BP_Door_02a2. Its far side is our own interior wall (SM_Wall_3_5x2m_01b8 and
SM_wall_4x4m_01c9 sit 30-80 cm behind the frame) with no floor beyond it for 8 m
(Saved/WorldExpansion/Door02a2_Beyond_20261001.json), so the door must not open. Adds the CarnivalSealedDoor tag
that UCarnivalDoorSubsystem honours. Backs up and saves only the door's own level."""
import hashlib
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/SealDoor02a2_20261001"
OUT.mkdir(parents=True, exist_ok=False)
MAIN_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
TAG = unreal.Name("CarnivalSealedDoor")
R = {"success": False, "errors": []}
try:
    R["main_sha256_before"] = hashlib.sha256(MAIN_FILE.read_bytes()).hexdigest()
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    doors = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
             if a.get_actor_label() == "BP_Door_02a2"]
    assert len(doors) == 1, "expected one BP_Door_02a2, found %d" % len(doors)
    door = doors[0]
    package = door.get_outermost()
    pkg_name = package.get_name()
    level_file = ROOT / ("Content" + pkg_name[len("/Game"):] + ".umap")
    shutil.copy2(level_file, OUT / (level_file.stem + ".before_seal.umap"))
    tags = list(door.get_editor_property("tags"))
    assert TAG not in tags, "already sealed"
    door.modify()
    door.set_editor_property("tags", tags + [TAG])
    assert unreal.EditorLoadingAndSavingUtils.save_packages([package], False), "save failed"
    R.update(level=pkg_name, location=door.get_actor_location().to_tuple(),
             tags=[str(t) for t in door.get_editor_property("tags")])
    R["main_sha256_after"] = hashlib.sha256(MAIN_FILE.read_bytes()).hexdigest()
    assert R["main_sha256_after"] == R["main_sha256_before"], "persistent map changed"
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
(OUT / "index.json").write_text(json.dumps(R, indent=1, default=str))
print("SEAL_DOOR_DONE")
