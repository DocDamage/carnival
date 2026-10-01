"""Remove the spruce that grows up through Lab A's main room. It is foliage instance #3868, rooted at
(-41762, -5730, -553) in the Day, Night and NightSnow lighting levels (two snow foliage types in NightSnow;
Saved/WorldExpansion/LabASpruce_LightingLevels_20261001.json). Removal goes through
UCarnivalRouteEditorLibrary.remove_foliage_in_box (the foliage system's own RemoveInstances), limited to a 1 m box
around that root and to spruce meshes. Each level is backed up, saved, reloaded and re-checked."""
import hashlib
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/LabASpruceRemoval_v4_20261001"  # v1 cleaned Day and Night; v2 removed NightSnow's recorded copy (original backed up in v2)
OUT.mkdir(parents=True, exist_ok=False)
ROOT_CM = (-41762.0, -5730.0, -553.0)
LO = unreal.Vector(ROOT_CM[0] - 50, ROOT_CM[1] - 50, ROOT_CM[2] - 300)  # foliage types may store the root offset vertically
HI = unreal.Vector(ROOT_CM[0] + 50, ROOT_CM[1] + 50, ROOT_CM[2] + 300)
EXPECTED = {"Lv_LightingDay": 1, "Lv_LightingNight": 1, "Lv_LightingNightSnow": 2}
MAIN_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
R = {"success": False, "errors": [], "levels": {}}


def spruce_left(world_actors):
    left = 0
    for ifa in [a for a in world_actors if a.get_class().get_name() == "InstancedFoliageActor"]:
        for comp in ifa.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not comp.static_mesh or "Spruce" not in comp.static_mesh.get_name():
                continue
            for i in range(comp.get_instance_count()):
                p = comp.get_instance_transform(i, True).translation
                if LO.x <= p.x <= HI.x and LO.y <= p.y <= HI.y and LO.z <= p.z <= HI.z:
                    left += 1
    return left


try:
    R["main_sha256_before"] = hashlib.sha256(MAIN_FILE.read_bytes()).hexdigest()
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for name, expected in EXPECTED.items():
        package = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/" + name
        f = ROOT / ("Content" + package[len("/Game"):] + ".umap")
        shutil.copy2(f, OUT / (name + ".before_spruce.umap"))
        world = unreal.EditorLoadingAndSavingUtils.load_map(package)
        if spruce_left(EAS.get_all_level_actors()) == 0:
            R["levels"][name] = {"already_clean": True}
            continue
        removed = 0
        for ifa in [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == "InstancedFoliageActor"]:
            n = unreal.CarnivalRouteEditorLibrary.remove_foliage_in_box(ifa, LO, HI, "Spruce")
            assert n >= 0, "removal refused in " + name
            removed += n
        # NightSnow lists the tree in two snow components but one foliage record may own both; the reload check below
        # is what proves the tree is gone.
        # NightSnow also holds the tree in an orphan component no foliage record owns (stale vendor duplicate,
        # LabASpruce_NightSnowRecords_20261001.json). Nothing tracks it, so remove its instances directly.
        for ifa in [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == "InstancedFoliageActor"]:
            orphans = {str(l).split()[1] for l in unreal.CarnivalRouteEditorLibrary.describe_foliage_in_box(ifa, LO, HI)
                       if str(l).startswith("component") and "owned_by_record=NO" in str(l)}
            for comp in ifa.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if comp.get_name() not in orphans or not comp.static_mesh or "Spruce" not in comp.static_mesh.get_name():
                    continue
                inside = [i for i in range(comp.get_instance_count())
                          if all(lo <= v <= hi for lo, v, hi in zip(LO.to_tuple(), comp.get_instance_transform(i, True).translation.to_tuple(), HI.to_tuple()))]
                for i in sorted(inside, reverse=True):
                    assert comp.remove_instance(i), "orphan instance removal failed"
                ifa.modify()
                R.setdefault("orphan_removed", []).append({"level": name, "component": comp.get_name(), "removed": len(inside)})
                removed += len(inside)
        assert 1 <= removed <= expected, "%s: removed %d, expected 1..%d" % (name, removed, expected)
        assert unreal.EditorLoadingAndSavingUtils.save_map(world, package), "save failed: " + name
        world = unreal.EditorLoadingAndSavingUtils.load_map(package)
        left = spruce_left(EAS.get_all_level_actors())
        assert left == 0, "%s: %d spruce instances still at the root after reload" % (name, left)
        R["levels"][name] = {"removed": removed, "left_after_reload": left}
    R["main_sha256_after"] = hashlib.sha256(MAIN_FILE.read_bytes()).hexdigest()
    assert R["main_sha256_after"] == R["main_sha256_before"], "persistent map changed"
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
(OUT / "index.json").write_text(json.dumps(R, indent=1))
print("LAB_SPRUCE_REMOVAL_DONE")
