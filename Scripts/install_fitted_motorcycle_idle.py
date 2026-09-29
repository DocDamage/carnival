"""Install the fitted local riding idle with a reversible player Blueprint backup."""
import json
import shutil
from datetime import datetime
from pathlib import Path
import unreal
base='/Game/Carnival/Vehicles/Motorcycle/Fitted'
clip=unreal.load_asset(base+'/Bike_Fitted_Idle')
assert clip
path=base+'/AM_Bike_Fitted_Idle'
montage=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
if not montage:
    factory=unreal.AnimMontageFactory()
    factory.set_editor_property('source_animation',clip)
    factory.set_editor_property('target_skeleton',clip.get_editor_property('skeleton'))
    montage=unreal.AssetToolsHelpers.get_asset_tools().create_asset('AM_Bike_Fitted_Idle',base,unreal.AnimMontage,factory)
assert montage
unreal.EditorAssetLibrary.save_loaded_asset(montage,False)
root=Path(r'F:\Carnival')
backup=root/'Saved/DirtBike'/('FittedIdleBackup_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.uasset')
shutil.copy2(root/'Content/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.uasset',backup)
bp=unreal.load_asset('/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter')
cdo=unreal.get_default_object(bp.generated_class())
old=cdo.get_editor_property('riding_idle_montage')
cdo.set_editor_property('riding_idle_montage',montage)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
(root/'Saved/DirtBike/Fitted_Idle_Install.json').write_text(json.dumps({'backup':str(backup),'previous':old.get_path_name(),'montage':path},indent=2))
