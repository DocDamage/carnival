"""Read-only: every streaming level's saved transform in the connected root map."""
import json
from pathlib import Path
import unreal
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
rows=[]
for lv in unreal.EditorLevelUtils.get_levels(world):
 pkg=lv.get_outermost().get_name()
 s=unreal.GameplayStatics.get_streaming_level(world,pkg)
 if not s:continue
 t=s.get_editor_property('level_transform');r=t.rotation.rotator()
 rows.append({'package':pkg,'class':s.get_class().get_name(),'location':list(t.translation.to_tuple()),
  'roll':r.roll,'pitch':r.pitch,'yaw':r.yaw,'scale':list(t.scale3d.to_tuple())})
Path(r'F:\Carnival\Saved\CampaignAcceptance\StreamingLevelTransforms_20260930.json').write_text(json.dumps(rows,indent=1))
