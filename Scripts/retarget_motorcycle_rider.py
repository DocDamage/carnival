"""Create local Manny-proportioned bike clips using the existing ride retarget rig."""
import json
from pathlib import Path
import unreal
base='/Game/Carnival/Vehicles/Motorcycle/Fitted'
source=unreal.load_asset('/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple')
target=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
retarget=unreal.load_asset('/Game/Carnival/Rides/Retarget/RTG_RidePose_Player')
assert source and target and retarget
registry=unreal.AssetRegistryHelpers.get_asset_registry()
clips=['AS_Idle_Riding','AS_Mount_Left','AS_Mount_Right','AS_Dismount_Left','AS_Dismount_Right']
report=[]
for name in clips:
    path=base+'/Bike_'+name
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        inputs=unreal.IKRetargetBatchOperationInputs()
        inputs.assets_to_retarget=registry.get_assets_by_package_name('/Game/Carnival/Vehicles/Motorcycle/Animations/'+name)
        inputs.source_mesh=source; inputs.target_mesh=target; inputs.ik_retarget_asset=retarget
        inputs.prefix='Bike_'; inputs.target_path=base
        inputs.include_referenced_assets=False; inputs.overwrite_existing_files=False
        results=unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
        assert len(results)==1,results
    clip=unreal.load_asset(path)
    assert clip and clip.get_editor_property('skeleton')==target.get_editor_property('skeleton')
    clip.set_editor_property('enable_root_motion',False)
    clip.set_editor_property('force_root_lock',True)
    unreal.EditorAssetLibrary.save_loaded_asset(clip,False)
    report.append(clip.get_path_name())
Path(r'F:\Carnival\Saved\DirtBike\Rider_Retarget.json').write_text(json.dumps(report,indent=2))
