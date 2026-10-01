"""Read-only: foliage records and components holding instances at the Lab A spruce root in Lv_LightingNightSnow
(UCarnivalRouteEditorLibrary.describe_foliage_in_box), to see why one instance resists record-based removal."""
import json
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\WorldExpansion\LabASpruce_NightSnowRecords_20261001.json")
LO = unreal.Vector(-41812, -5780, -853)
HI = unreal.Vector(-41712, -5680, -253)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/Lv_LightingNightSnow")
rows = []
for ifa in [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
            if a.get_class().get_name() == "InstancedFoliageActor"]:
    for line in unreal.CarnivalRouteEditorLibrary.describe_foliage_in_box(ifa, LO, HI):
        line = str(line)
        if line.startswith("component") or "inside=0" not in line or "Spruce" in line:
            rows.append(ifa.get_actor_label() + ": " + line)
OUT.write_text(json.dumps(rows, indent=1))
print("SPRUCE_RECORDS_DONE")
