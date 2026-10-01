"""Read-only bounds of candidate marker meshes."""
import json,unreal
out={}
for p in open(r'C:\Users\dferr\AppData\Local\Temp\marker_meshes.txt').read().split():
 b=unreal.load_asset(p).get_bounds();out[p]={'origin':list(b.origin.to_tuple()),'extent':list(b.box_extent.to_tuple())}
for p in ['/Game/Carnival/WorldExpansion/IndustrialSwitchboard/SM_IndustrialSwitchboard.SM_IndustrialSwitchboard','/Game/Docks/VOL2_Powell/Meshes/SM_SwitchBox.SM_SwitchBox','/Game/Town/Meshes/Props/SM_TableDesk.SM_TableDesk','/Game/SciFiWorld/Meshes/SM_ControlPanel01.SM_ControlPanel01','/Game/UnderwaterShip/Meshes/Props/CabinMetal/SM_LargeChest.SM_LargeChest']:
 b=unreal.load_asset(p).get_bounds();out[p]={'origin':list(b.origin.to_tuple()),'extent':list(b.box_extent.to_tuple())}
open(r'F:\Carnival\Saved\CampaignAcceptance\MarkerMeshBounds_20260930.json','w').write(json.dumps(out,indent=1))
