"""Create reusable UE4-to-doll IK assets and a small, useful pack sample set."""
import json, math
from pathlib import Path
import unreal

BASE='/Game/Carnival/Characters/PossessedDoll'
OUT=Path(r'F:\Carnival\Saved\HauntedDollIntegration')
eal=unreal.EditorAssetLibrary
tools=unreal.AssetToolsHelpers.get_asset_tools()
target=unreal.load_asset(BASE+'/SK_Doll')
source=unreal.load_asset('/Game/RamsterZ_FreeAnims_Volume1/Demo/Mannequin/Character/Mesh/SK_Mannequin')
assert target and source
chains=[('Spine','spine_01','spine_03','spine_02'),('Neck','neck_01','neck_01','neck_01'),('Head','head','head','head')]
for side in ['l','r']:
    chains += [(f'Clavicle_{side}',f'clavicle_{side}',f'clavicle_{side}',f'clavicle_{side}'),
               (f'Arm_{side}',f'upperarm_{side}',f'hand_{side}',f'hand_{side}'),
               (f'Leg_{side}',f'thigh_{side}',f'foot_{side}',f'foot_{side}')]

def make_rig(name,mesh,is_target):
    rig=unreal.load_asset(BASE+'/Retarget/'+name) if eal.does_asset_exist(BASE+'/Retarget/'+name) else tools.create_asset(name,BASE+'/Retarget',unreal.IKRigDefinition,unreal.IKRigDefinitionFactory())
    c=unreal.IKRigController.get_controller(rig)
    assert c.set_skeletal_mesh(mesh)
    assert c.set_retarget_root('pelvis')
    assert c.set_root_motion_bone('root')
    existing={str(ch.chain_name) for ch in c.get_retarget_chains()}
    for name,start,src_end,tgt_end in chains:
        if name not in existing:c.add_retarget_chain(name,start,tgt_end if is_target else src_end,'None')
    eal.save_loaded_asset(rig)
    return rig

src=make_rig('IK_RamsterZ_UE4',source,False)
tgt=make_rig('IK_PossessedDoll',target,True)
path=BASE+'/Retarget/RTG_RamsterZ_To_Doll'
rtg=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset('RTG_RamsterZ_To_Doll',BASE+'/Retarget',unreal.IKRetargeter,unreal.IKRetargetFactory())
c=unreal.IKRetargeterController.get_controller(rtg)
S=unreal.RetargetSourceOrTarget.SOURCE;T=unreal.RetargetSourceOrTarget.TARGET
c.set_ik_rig(S,src);c.set_ik_rig(T,tgt)
c.set_preview_mesh(S,source);c.set_preview_mesh(T,target)
if c.get_num_retarget_ops()==0:c.add_default_ops()
c.assign_ik_rig_to_all_ops(S,src);c.assign_ik_rig_to_all_ops(T,tgt)
c.auto_map_chains(unreal.AutoMapChainType.EXACT,True)
for i in range(c.get_num_retarget_ops()):
    name=str(c.get_op_name(i))
    # These source gestures need proportional FK transfer. No IK solvers/goals
    # are fabricated; limb IK can be added later for contact-heavy choreography.
    if name in ['IK Chains','IK Solve','Run IK Rig']:c.set_retarget_op_enabled(i,False)
pose_name='Doll_Aligned_To_UE4'
if pose_name not in [str(n) for n in c.get_retarget_poses(T)]:c.create_retarget_pose(pose_name,T)
c.set_current_retarget_pose(pose_name,T)
c.reset_retarget_pose(pose_name,[],T)
c.auto_align_all_bones(T,unreal.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
eal.save_loaded_asset(rtg)

registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.wait_for_completion()
wanted={'Standing_Idle','Stealth_Idle','TalkGesture_Dramatic01','TalkGesture_Dramatic02'}
assets=[a for a in registry.get_assets_by_path('/Game/RamsterZ_FreeAnims_Volume1/AnimationSequence',True) if str(a.asset_name) in wanted]
assert len(assets)==4,len(assets)
inputs=unreal.IKRetargetBatchOperationInputs()
inputs.assets_to_retarget=assets;inputs.source_mesh=source;inputs.target_mesh=target;inputs.ik_retarget_asset=rtg
inputs.prefix='Doll_RZ_';inputs.target_path=BASE+'/Animations/RamsterZ_Volume1'
inputs.include_referenced_assets=False;inputs.overwrite_existing_files=True
results=unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
assert len(results)==4,len(results)
evaluation=unreal.AnimPoseEvaluationOptions()
evaluation.optional_skeletal_mesh=target
evaluation.incorporate_root_motion_into_pose=True
report={'retargeter':path,'chains':{ch[0]:str(c.get_source_chain(ch[0])) for ch in chains},
        'ops':[{'name':str(c.get_op_name(i)), 'enabled':c.get_retarget_op_enabled(i)} for i in range(c.get_num_retarget_ops())],'clips':[]}
for asset in results:
    a=asset.get_asset()
    assert a.get_editor_property('skeleton')==target.skeleton
    a.set_editor_property('enable_root_motion',False)
    a.set_editor_property('force_root_lock',True)
    a.set_editor_property('root_motion_root_lock',unreal.RootMotionRootLock.ANIM_FIRST_FRAME)
    duration=a.get_editor_property('sequence_length')
    sample=[]
    for f in [0,.25,.5,.75,1]:
        p=unreal.AnimPoseExtensions.get_anim_pose_at_time(a,duration*f,evaluation)
        bones={str(n):p.get_bone_pose(n,unreal.AnimPoseSpaces.WORLD) for n in p.get_bone_names()}
        for bone,tx in bones.items():
            assert all(math.isfinite(v) for v in [tx.translation.x,tx.translation.y,tx.translation.z]),(a,bone)
            assert .98<tx.scale3d.x<1.02 and .98<tx.scale3d.y<1.02 and .98<tx.scale3d.z<1.02,(a,bone,str(tx))
        sample.append({'fraction':f,'bones':{n:str(tx) for n,tx in bones.items()}})
    eal.save_loaded_asset(a)
    report['clips'].append({'path':a.get_path_name(),'seconds':duration,'samples':sample})
(OUT/'RamsterZ_Unreal_Retarget.json').write_text(json.dumps(report,indent=2))
unreal.log_warning('DOLL_RAMSTERZ_RETARGET_COMPLETE '+str(len(results)))
