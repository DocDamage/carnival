"""Remove the editor-only F1-F7 map-travel shortcuts (B14). They opened standalone maps: five of the seven regions
were cut from the demo on 2026-09-30, and F2 loaded the vendor's source mansion instead of the connected one.
Unmaps IA_Travel* from IMC_CarnivalPlayer and IMC_CarnivalMotorcycle, clears the controller Blueprint's travel
action properties, then deletes the seven actions once nothing else references them. Backs up every changed asset."""
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/InputCleanup/RemoveFastTravel_v3_20261001"  # v1 cleared the controller properties; v2 unmapped F1-F7; v3 deletes
OUT.mkdir(parents=True, exist_ok=False)
EAL = unreal.EditorAssetLibrary
INPUT = "/Game/Carnival/Input"
PLACES = ["Carnival", "Mansion", "Town", "Lighthouse", "Castle", "Arena", "Mars"]
ACTIONS = [INPUT + "/IA_Travel" + p for p in PLACES]
CONTEXTS = [INPUT + "/IMC_CarnivalPlayer", INPUT + "/IMC_CarnivalMotorcycle"]
CONTROLLER = "/Game/Carnival/Blueprints/BP_CarnivalPlayerController"
R = {"success": False, "errors": [], "unmapped": [], "cleared": [], "deleted": []}


def backup(path):
    f = ROOT / ("Content" + path[len("/Game"):] + ".uasset")
    shutil.copy2(f, OUT / f.name)


try:
    actions = {a: unreal.load_asset(a) for a in ACTIONS}
    assert all(actions.values()), "missing travel action"
    for c in CONTEXTS:
        backup(c)
        ctx = unreal.load_asset(c)
        try:  # UE 5.8 keeps the mappings in default_key_mappings
            mappings = list(ctx.get_editor_property("default_key_mappings").get_editor_property("mappings"))
        except Exception:
            mappings = list(ctx.get_editor_property("mappings"))
        R.setdefault("mapping_counts", {})[c] = len(mappings)
        for m in mappings:
            act = m.get_editor_property("action")
            if act and act.get_path_name().split(".")[0] in ACTIONS:
                key = m.get_editor_property("key")
                ctx.unmap_key(act, key)
                R["unmapped"].append({"context": c, "action": act.get_name(), "key": str(key.get_editor_property("key_name"))})
        assert EAL.save_loaded_asset(ctx, False), "save failed " + c
    backup(CONTROLLER)
    bp = unreal.load_asset(CONTROLLER)
    cdo = unreal.get_default_object(bp.generated_class())
    for p in PLACES:
        prop = "travel_%s_action" % p.lower()
        cdo.set_editor_property(prop, None)
        R["cleared"].append(prop)
    assert EAL.save_loaded_asset(bp, False), "controller save failed"
    for a in ACTIONS:
        refs = [r for r in EAL.find_package_referencers_for_asset(a, False) if r.split(".")[0] not in ACTIONS]
        assert not refs, a + " still referenced by " + str(refs)
        backup(a)
        assert EAL.delete_asset(a), "delete failed " + a
        R["deleted"].append(a)
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
(OUT / "index.json").write_text(json.dumps(R, indent=1))
print("REMOVE_FAST_TRAVEL_DONE")
