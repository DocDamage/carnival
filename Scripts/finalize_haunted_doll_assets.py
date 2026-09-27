"""Finalize generated asset settings and test-map orientation, without changing source packs."""
import unreal
BASE='/Game/Carnival/Characters/PossessedDoll'
eal=unreal.EditorAssetLibrary
world=unreal.EditorLoadingAndSavingUtils.load_map(BASE+'/Maps/L_DollTest')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    label=a.get_actor_label()
    if label in ['PlayerStart_DollTest','DollTest_PreviewCamera'] or isinstance(a,unreal.DirectionalLight):
        a.modify();a.get_editor_property('root_component').modify()
    if label=='PlayerStart_DollTest': a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=180,roll=0),False)
    if label=='DollTest_PreviewCamera': a.set_actor_rotation(unreal.Rotator(pitch=-12,yaw=141,roll=0),False)
    if isinstance(a,unreal.DirectionalLight): a.set_actor_rotation(unreal.Rotator(pitch=-45,yaw=-35,roll=0),False)
assert unreal.EditorLoadingAndSavingUtils.save_map(world,BASE+'/Maps/L_DollTest')
for name in ['M_Doll_Body','M_Doll_Legs']:
    m=unreal.load_asset(BASE+'/Materials/'+name)
    m.set_editor_property('used_with_skeletal_mesh',True)
    eal.save_loaded_asset(m)
rtg=unreal.load_asset(BASE+'/Retarget/RTG_RamsterZ_To_Doll')
c=unreal.IKRetargeterController.get_controller(rtg)
for i in range(c.get_num_retarget_ops()):
    if str(c.get_op_name(i))=='Run IK Rig':c.set_retarget_op_enabled(i,False)
eal.save_loaded_asset(rtg)
# Remove only the two scratch assets made by the initial importer probe, and
# only when nothing outside that scratch pair references either package.
scratch=[BASE+'/SK_PossessedDoll',BASE+'/SK_PossessedDoll_Skeleton']
external=[]
for path in scratch:
    if eal.does_asset_exist(path): external += [p for p in eal.find_package_referencers_for_asset(path,False) if p not in scratch]
if not external:
    for path in scratch:
        if eal.does_asset_exist(path):assert eal.delete_asset(path)
unreal.log_warning('DOLL_ASSET_FINALIZATION_COMPLETE')
