"""Let authored riding poses bypass floor correction in a local player AnimBP copy."""
import json
import shutil
from datetime import datetime
from pathlib import Path
import unreal
eal=unreal.EditorAssetLibrary
source='/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Animations/ABP_Manny'
dest='/Game/Carnival/Character/Animations/ABP_CarnivalManny'
bp=unreal.load_asset(dest) if eal.does_asset_exist(dest) else eal.duplicate_asset(source,dest)
assert bp
count=unreal.CarnivalVehicleAuthoring.configure_mounted_foot_rig(bp)
assert count==1, count
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert bp.get_editor_property('status')==unreal.BlueprintStatus.BS_UP_TO_DATE,bp.get_editor_property('status')
eal.save_loaded_asset(bp,False)
root=Path(r'F:\Carnival')
backup=root/'Saved/DirtBike'/('MountedGraphBackup_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.uasset')
shutil.copy2(root/'Content/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.uasset',backup)
player=unreal.load_asset('/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter')
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(player):
    component=unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle))
    if isinstance(component,unreal.SkeletalMeshComponent) and component.get_name()=='CharacterMesh0':
        component.set_editor_property('anim_class',bp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(player)
eal.save_loaded_asset(player,False)
(root/'Saved/DirtBike/Mounted_Graph_Setup.json').write_text(json.dumps({'asset':dest,'control_rig_nodes':count,'alpha':'1 - DisableLegIK','player_backup':str(backup)},indent=2))
