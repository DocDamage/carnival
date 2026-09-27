"""Create the reusable attendant, seated clip and a small playable swing test map.

The staff mesh is a visible mannequin prototype pending final human casting.
The vendor ride and source animation assets are never rebuilt or overwritten.
"""
import json
import shutil
from pathlib import Path
import unreal

BASE = '/Game/Carnival/Rides'
OUT = Path(r'F:\Carnival\Saved\RideDevelopment')
OUT.mkdir(parents=True, exist_ok=True)
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDFL = unreal.SubobjectDataBlueprintFunctionLibrary

def backup(path):
    for extension in ('.uasset', '.umap'):
        relative = path.removeprefix('/Game/') + extension
        source = Path(r'F:\Carnival\Content') / relative
        dest = OUT / 'BeforeAttendedRides' / relative
        if source.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)

def asset(name, folder, cls, factory):
    path = folder + '/' + name
    return unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(name, folder, cls, factory)

source = unreal.load_asset('/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple')
target = unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
chains = [('Spine','spine_01','spine_05'), ('Neck','neck_01','neck_02'), ('Head','head','head')]
for side in ('l','r'):
    chains += [(f'Clavicle_{side}',f'clavicle_{side}',f'clavicle_{side}'), (f'Arm_{side}',f'upperarm_{side}',f'hand_{side}'),
               (f'Leg_{side}',f'thigh_{side}',f'ball_{side}')]
    for digit in ('thumb','index','middle','ring','pinky'):
        chains.append((digit+'_'+side, digit+'_01_'+side,digit+'_03_'+side))

def rig(name, mesh):
    result = asset(name, BASE+'/Retarget', unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    c = unreal.IKRigController.get_controller(result)
    assert c.set_skeletal_mesh(mesh)
    c.set_retarget_root('pelvis'); c.set_root_motion_bone('root')
    existing = {str(ch.chain_name) for ch in c.get_retarget_chains()}
    for name, first, last in chains:
        if name not in existing: c.add_retarget_chain(name,first,last,'None')
    EAL.save_loaded_asset(result, False)
    return result

src = rig('IK_RidePose_Source', source)
tgt = rig('IK_RidePose_Player', target)
retarget = asset('RTG_RidePose_Player', BASE+'/Retarget', unreal.IKRetargeter, unreal.IKRetargetFactory())
controller = unreal.IKRetargeterController.get_controller(retarget)
S = unreal.RetargetSourceOrTarget.SOURCE; T = unreal.RetargetSourceOrTarget.TARGET
controller.set_ik_rig(S,src); controller.set_ik_rig(T,tgt)
controller.set_preview_mesh(S,source); controller.set_preview_mesh(T,target)
if controller.get_num_retarget_ops() == 0: controller.add_default_ops()
controller.assign_ik_rig_to_all_ops(S,src); controller.assign_ik_rig_to_all_ops(T,tgt)
controller.auto_map_chains(unreal.AutoMapChainType.EXACT,True)
for i in range(controller.get_num_retarget_ops()):
    if str(controller.get_op_name(i)) in ('IK Chains','IK Solve','Run IK Rig'): controller.set_retarget_op_enabled(i,False)
EAL.save_loaded_asset(retarget,False)
seated_path = BASE+'/Animations/Ride_AS_Sit_01'
if not EAL.does_asset_exist(seated_path):
    inputs = unreal.IKRetargetBatchOperationInputs()
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    inputs.assets_to_retarget = registry.get_assets_by_package_name('/Game/FreeAnimationLibrary/Animations/Update_2/Chair/AS_Sit_01')
    inputs.source_mesh=source; inputs.target_mesh=target; inputs.ik_retarget_asset=retarget
    inputs.prefix='Ride_'; inputs.target_path=BASE+'/Animations'
    inputs.include_referenced_assets=False; inputs.overwrite_existing_files=False
    results = unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
    assert len(results)==1, results
clip = unreal.load_asset(seated_path)
assert clip and clip.get_editor_property('skeleton') == target.get_editor_property('skeleton')
clip.set_editor_property('enable_root_motion',False)
clip.set_editor_property('force_root_lock',True)
EAL.save_loaded_asset(clip,False)
player_path='/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter'
backup(player_path)
player_bp=unreal.load_asset(player_path)
player_cdo=unreal.get_default_object(player_bp.generated_class())
player_cdo.set_editor_property('ride_seated_animation',clip)
unreal.BlueprintEditorLibrary.compile_blueprint(player_bp)
EAL.save_loaded_asset(player_bp,False)

factory=unreal.BlueprintFactory()
factory.set_editor_property('parent_class',unreal.CarnivalRideAttendant)
staff_bp=asset('BP_RideAttendant',BASE,unreal.Blueprint,factory)
staff_cdo=unreal.get_default_object(staff_bp.generated_class())
staff_cdo.set_editor_property('idle_animation',unreal.load_asset('/Game/FreeAnimationLibrary/Animations/Idle/anim_Idle'))
staff_cdo.set_editor_property('operate_animation',unreal.load_asset('/Game/FreeAnimationLibrary/Animations/Interaction/anim_PushButton_R'))
for handle in SDS.k2_gather_subobject_data_for_blueprint(staff_bp):
    component=SDFL.get_associated_object(SDFL.get_data(handle))
    if isinstance(component,unreal.SkeletalMeshComponent): component.set_skeletal_mesh_asset(source)
unreal.BlueprintEditorLibrary.compile_blueprint(staff_bp)
EAL.save_loaded_asset(staff_bp,False)

# Match the seated pelvis to the chair anchor, keeping capsule origin above it.
swing_path=BASE+'/BP_Swing_Carnival'
backup(swing_path)
swing_bp=unreal.load_asset(swing_path)
for handle in SDS.k2_gather_subobject_data_for_blueprint(swing_bp):
    component=SDFL.get_associated_object(SDFL.get_data(handle))
    if isinstance(component,unreal.CarnivalRideSeatComponent):
        component.set_editor_property('passenger_offset',unreal.Transform(location=unreal.Vector(17,0,50)))
unreal.BlueprintEditorLibrary.compile_blueprint(swing_bp)
EAL.save_loaded_asset(swing_bp,False)

map_path=BASE+'/Maps/L_AttendedSwingTest'
if EAL.does_asset_exist(map_path):
    world=unreal.EditorLoadingAndSavingUtils.load_map(map_path)
else:
    world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    floor=ACTORS.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-25))
    floor.set_actor_label('RideTest_Ground')
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    floor.set_actor_scale3d(unreal.Vector(90,90,.5))
    sun=ACTORS.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,2500),unreal.Rotator(pitch=-45,yaw=-35,roll=0))
    sun.light_component.set_editor_property('intensity',4.0)
    sky=ACTORS.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,1000))
    sky.light_component.set_editor_property('intensity',1.0)
    ACTORS.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector())
    ride=ACTORS.spawn_actor_from_class(swing_bp.generated_class(),unreal.Vector())
    ride.set_actor_label('Swing_Attended_Test')
    staff=ACTORS.spawn_actor_from_class(staff_bp.generated_class(),unreal.Vector(1950,0,90),unreal.Rotator(yaw=180))
    staff.set_actor_label('Attendant_Swing_Test')
    staff.set_editor_property('ride',ride)
    staff.set_editor_property('ride_name',unreal.Text('Creepwood Swing'))
    ACTORS.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(2200,0,105),unreal.Rotator(yaw=180))
    world.get_world_settings().set_editor_property('default_game_mode',unreal.load_class(None,'/Game/Carnival/Blueprints/BP_CarnivalGameMode.BP_CarnivalGameMode_C'))
assert unreal.EditorLoadingAndSavingUtils.save_map(world,map_path)
(OUT/'Swing_Setup.json').write_text(json.dumps({'map':map_path,'attendant':staff_bp.get_path_name(),'seated_clip':clip.get_path_name(),'staff_visual':'Manny prototype; final human staff casting pending'},indent=2))
unreal.log('SWING_ATTENDANT_SETUP_COMPLETE')
