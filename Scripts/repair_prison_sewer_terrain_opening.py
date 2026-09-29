"""Paint a real stair opening in the copied coastal terrain; preserve source assets."""
import datetime,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion'
PACKAGE='/Game/Carnival/World/Levels/L_CoastalMansionApproach'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=OUT/'Backups'/('L_CoastalMansionApproach_before_stair_opening_'+stamp+'.umap')
shutil.copy2(ROOT/'Content/Carnival/World/Levels/L_CoastalMansionApproach.umap',backup)
report={'success':False,'backup':str(backup),'changes':[]}
try:
    world=unreal.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    landscape=next(a for a in eas.get_all_level_actors() if a.get_actor_label()=='Landscape2')
    assetlib=unreal.EditorAssetLibrary; ml=unreal.MaterialEditingLibrary
    master_path='/Game/Carnival/World/Materials/M_CoastalStairHole'
    instance_path='/Game/Carnival/World/Materials/MI_CoastalStairHole'
    if not assetlib.does_asset_exist(master_path):
        master=assetlib.duplicate_asset('/Game/RailBridge/Materials/Master/M_Landscape',master_path)
        if not master: raise RuntimeError('Cannot duplicate coastal master')
    master=unreal.load_asset(master_path)
    if master.get_editor_property('blend_mode') != unreal.BlendMode.BLEND_MASKED:
        if not unreal.CarnivalRouteEditorLibrary.add_landscape_visibility_mask(master):
            raise RuntimeError('Cannot preserve material attributes while adding visibility mask')
        ml.recompile_material(master)
        if not assetlib.save_loaded_asset(master): raise RuntimeError('Cannot save hole master')
    master=unreal.load_asset(master_path)
    if not assetlib.does_asset_exist(instance_path):
        instance=assetlib.duplicate_asset('/Game/RailBridge/Materials/MI_Landscape_Inst',instance_path)
        ml.set_material_instance_parent(instance,master)
        if not assetlib.save_loaded_asset(instance): raise RuntimeError('Cannot save copied hole instance')
    landscape.set_editor_property('landscape_hole_material',unreal.load_asset(instance_path))
    layout=json.loads((ROOT/'Saved/MansionConnection/Route_Layout.json').read_text())
    transform=unreal.Transform(location=unreal.Vector(*layout['coast_origin']),rotation=unreal.Rotator(pitch=0,yaw=layout['coast_yaw'],roll=0),scale=unreal.Vector(1,1,1))
    minimum=unreal.Vector(-27350,-17650,-2000); maximum=unreal.Vector(-26650,-14700,2000)
    if not unreal.CarnivalRouteEditorLibrary.cut_landscape_opening(landscape,minimum,maximum,transform): raise RuntimeError('Landscape opening rejected (ownership, bounds, or paint data)')
    landscape.force_layers_full_update()
    for a in eas.get_all_level_actors():
        if a.get_actor_label()=='SM_buoy_01a4' and 'StairClearanceMoved' not in [str(t) for t in a.get_editor_property('tags')]:
            before=a.get_actor_location(); world_location=unreal.MathLibrary.transform_location(transform,before)
            after=unreal.MathLibrary.inverse_transform_location(transform,world_location+unreal.Vector(900,0,0))
            a.set_actor_location(after,False,True)
            a.set_editor_property('tags',list(a.get_editor_property('tags'))+[unreal.Name('StairClearanceMoved')])
            report['changes'].append({'buoy':a.get_path_name(),'before_local':before.to_tuple(),'after_local':after.to_tuple()})
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,PACKAGE): raise RuntimeError('Cannot save terrain opening')
    report.update(success=True,opening_world_min=minimum.to_tuple(),opening_world_max=maximum.to_tuple(),hole_material=instance_path,preserved_source_material=True)
except Exception:
    report['error']=traceback.format_exc()
    unreal.log_error(report['error'])
finally:
    (OUT/'Prison_Sewer_Terrain_Opening_Repair.json').write_text(json.dumps(report,indent=2,default=str))
    unreal.SystemLibrary.quit_editor()
