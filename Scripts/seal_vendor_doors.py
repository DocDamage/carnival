"""Seal vendor doors that open onto solid geometry, by adding the CarnivalSealedDoor tag that
UCarnivalDoorSubsystem honours. Doors come from CARNIVAL_SEAL_DOORS (comma-separated labels), default BP_Door_02a2.
Evidence for each is a probe_door_02a2_beyond.py report:
- BP_Door_02a2 (hospital): our interior walls 30-80 cm behind the frame, no floor beyond for 8 m.
- BP_Door11 (mansion balcony): the outer-wall door frame's collision fills the opening; vendor barriers inside.
- BP_Door12 (mansion top floor): set in a solid wall, on a floor no stair reaches.
Backs up and saves only the doors' own levels; the persistent map hash is checked unchanged."""
import os
import hashlib
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
LABELS = os.environ.get("CARNIVAL_SEAL_DOORS", "BP_Door_02a2").split(",")
OUT = ROOT / "Saved/WorldExpansion" / os.environ.get("CARNIVAL_SEAL_OUT", "SealDoor02a2_20261001")
OUT.mkdir(parents=True, exist_ok=False)
MAIN_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
TAG = unreal.Name("CarnivalSealedDoor")
R = {"success": False, "errors": []}
try:
    R["main_sha256_before"] = hashlib.sha256(MAIN_FILE.read_bytes()).hexdigest()
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    packages, R["doors"] = {}, []
    for label in LABELS:
        doors = [a for a in acts if a.get_actor_label() == label]
        assert len(doors) == 1, "expected one %s, found %d" % (label, len(doors))
        door = doors[0]
        package = door.get_outermost()
        pkg_name = package.get_name()
        if pkg_name not in packages:
            level_file = ROOT / ("Content" + pkg_name[len("/Game"):] + ".umap")
            shutil.copy2(level_file, OUT / (level_file.stem + ".before_seal.umap"))
            packages[pkg_name] = package
        tags = list(door.get_editor_property("tags"))
        assert TAG not in tags, label + " already sealed"
        door.modify()
        door.set_editor_property("tags", tags + [TAG])
        R["doors"].append({"door": label, "level": pkg_name, "location": door.get_actor_location().to_tuple()})
    assert unreal.EditorLoadingAndSavingUtils.save_packages(list(packages.values()), False), "save failed"
    R["main_sha256_after"] = hashlib.sha256(MAIN_FILE.read_bytes()).hexdigest()
    assert R["main_sha256_after"] == R["main_sha256_before"], "persistent map changed"
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
(OUT / "index.json").write_text(json.dumps(R, indent=1, default=str))
print("SEAL_DOOR_DONE")
