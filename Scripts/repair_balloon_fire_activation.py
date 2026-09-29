"""Preserve vendor assets and remove redundant runtime activation in a local base."""
import json
import shutil
from datetime import datetime
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/RideDevelopment'
SOURCE='/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/BP_HotairBalloon_Ride_01a'
ADAPTED='/Game/Carnival/Rides/Adapted/BP_HotAirBalloon_Runtime'
CHILD='/Game/Carnival/Rides/BP_HotAirBalloon_Carnival'
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
BACKUP=OUT/('BeforeBalloonFireRepair_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
REPORT={'vendor_asset_preserved':SOURCE,'adapted_base':ADAPTED,'child':CHILD,'backup':str(BACKUP),'success':False}
EAL=unreal.EditorAssetLibrary

def backup(package):
    for suffix in ('.uasset','.umap','.uexp','.ubulk'):
        relative=package.removeprefix('/Game/')+suffix
        source=ROOT/'Content'/relative; target=BACKUP/relative
        if source.exists():
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)

def snapshot():
    rows={}
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_class().get_name()!='BP_HotAirBalloon_Carnival_C': continue
        values={'actor':str(actor.get_actor_transform())}
        for component in actor.get_components_by_class(unreal.SceneComponent):
            if component.get_name()=='StaticMeshComponent1' or isinstance(component,unreal.CarnivalRideSeatComponent):
                values[component.get_name()]=str(component.get_world_transform())
        rows[actor.get_name()]=values
    return rows

world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
assert world
for package in (MAP,CHILD,ADAPTED): backup(package)
before=snapshot(); assert len(before)==10
adapted=unreal.load_asset(ADAPTED) if EAL.does_asset_exist(ADAPTED) else EAL.duplicate_asset(SOURCE,ADAPTED)
assert adapted
REPORT['before_graph']=list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(adapted))
REPORT['removed_nodes']=unreal.CarnivalBalloonFlightComponent.repair_redundant_fire_auto_activation(adapted)
assert REPORT['removed_nodes']>=0, 'FireSetup did not match the validated activation graph'
unreal.BlueprintEditorLibrary.compile_blueprint(adapted)
child=unreal.load_asset(CHILD)
unreal.BlueprintEditorLibrary.reparent_blueprint(child,adapted.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(child)
after=snapshot()
REPORT['geometry_before']=before
REPORT['geometry_after']=after
REPORT['geometry_preserved']=before==after
REPORT['after_graph']=list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(adapted))
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'Balloon_Fire_Repair.json').write_text(json.dumps(REPORT,indent=2))
assert REPORT['geometry_preserved'], 'Reparent changed placed transforms; inspect report before saving'
assert not any('bNewAutoActivate' in row for row in REPORT['after_graph'])
assert EAL.save_loaded_asset(adapted,False)
assert EAL.save_loaded_asset(child,False)
REPORT['success']=True
REPORT['saved_packages']=[ADAPTED,CHILD]
(OUT/'Balloon_Fire_Repair.json').write_text(json.dumps(REPORT,indent=2))
unreal.SystemLibrary.quit_editor()
