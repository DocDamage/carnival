"""Install fitted mount clips; hold their seated end until gameplay blends to idle."""
import json
import shutil
from datetime import datetime
from pathlib import Path
import unreal

base='/Game/Carnival/Vehicles/Motorcycle/Fitted'
root=Path(r'F:\Carnival')
backup=root/'Saved/DirtBike'/('FittedMountBackup_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.uasset')
shutil.copy2(root/'Content/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.uasset',backup)
bp=unreal.load_asset('/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter')
cdo=unreal.get_default_object(bp.generated_class())
report={'backup':str(backup),'assignments':[]}
for side in ['Left','Right']:
    clip=unreal.load_asset(base+'/Bike_Fitted_Mount_'+side)
    assert clip
    name='AM_Bike_Fitted_Mount_'+side
    path=base+'/'+name
    montage=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if not montage:
        factory=unreal.AnimMontageFactory()
        factory.set_editor_property('source_animation',clip)
        factory.set_editor_property('target_skeleton',clip.get_editor_property('skeleton'))
        montage=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,base,unreal.AnimMontage,factory)
    assert montage
    montage.set_editor_property('enable_auto_blend_out',False)
    assert unreal.EditorAssetLibrary.save_loaded_asset(montage,False)
    property_name='mount_'+side.lower()+'_montage'
    old=cdo.get_editor_property(property_name)
    cdo.set_editor_property(property_name,montage)
    report['assignments'].append({'property':property_name,'previous':old.get_path_name() if old else None,'new':path})
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
(root/'Saved/DirtBike/Fitted_Mount_Install.json').write_text(json.dumps(report,indent=2))
