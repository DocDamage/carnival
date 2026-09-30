"""Save distinct child-rig locomotion, gestures and a seated fitting source.

Uses the installed UE5.8 IK batch API already exercised by the doll pipeline.
Source animation/mesh assets and the separately supplied child skeletons stay
untouched. Numerical pose checks do not replace rendered gait or seat fitting.
"""
import json, math, os, traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
census=json.loads((OUT/'Child_Animation_Source_Census.json').read_text());assert census['success']
CANDIDATE=os.environ.get('CARNIVAL_CHILD_CONSISTENT_BIND')=='1'
REPORT_FILE='BlackBoy_ConsistentBind_Retarget.json' if CANDIDATE else 'Child_Roster_Retarget.json'
if CANDIDATE:
    candidate=json.loads((OUT/'BlackBoy_ConsistentBind_Import.json').read_text());assert candidate['success']
    census['children']=[dict(next(c for c in census['children'] if c['identity']=='BlackBoy'),mesh=candidate['mesh'])]
elif (OUT/'Child_Rig_Overrides.json').exists():
    overrides=json.loads((OUT/'Child_Rig_Overrides.json').read_text())
    census['children']=[dict(c,**{k:v for k,v in overrides.get(c['identity'],{}).items() if k in ('mesh','folder')}) for c in census['children']]
REPORT={'success':False,'children':[],'errors':[],
    'limits':'Saved IK retarget assets and finite sampled poses only. The bike seated source still needs chair/ride fitting. Actual gait, clothing, roaming, seating and rendered acceptance remain separate.'}
eal=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.wait_for_completion()
S=unreal.RetargetSourceOrTarget.SOURCE;T=unreal.RetargetSourceOrTarget.TARGET
GROUPS=[('Manny','/Game/PlayMusicAnim/Demo/Mannequins/Meshes/SKM_Manny',
    ['MM_Idle','MM_Walk_InPlace','MM_Run_Fwd']),
    ('RamsterZ','/Game/RamsterZ_FreeAnims_Volume1/Demo/Mannequin/Character/Mesh/SK_Mannequin',
    ['TalkGesture_Dramatic01','TalkGesture_Dramatic02']),
    ('SeatedSource','/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple',
    ['AS_Idle_Riding'])]

def chain_specs(bones,cc=False):
    spine=[b for b in ('spine_01','spine_02','spine_03','spine_04','spine_05') if b in bones]
    specs=[('Spine','Waist' if cc else spine[0],'Spine02' if cc else spine[-1]),
        ('Neck','NeckTwist01' if cc else 'neck_01','NeckTwist02' if cc else ('neck_02' if 'neck_02' in bones else 'neck_01')),
        ('Head','Head' if cc else 'head','Head' if cc else 'head')]
    for side,prefix in [('l','L'),('r','R')]:
        specs.extend([(f'Clavicle_{side}',prefix+'_Clavicle' if cc else 'clavicle_'+side,
                       prefix+'_Clavicle' if cc else 'clavicle_'+side),
            (f'Arm_{side}',prefix+'_Upperarm' if cc else 'upperarm_'+side,prefix+'_Hand' if cc else 'hand_'+side),
            (f'Leg_{side}',prefix+'_Thigh' if cc else 'thigh_'+side,prefix+'_Foot' if cc else 'foot_'+side)])
        for finger,target in [('thumb','Thumb'),('index','Index'),('middle','Mid'),('ring','Ring'),('pinky','Pinky')]:
            specs.append((finger+'_'+side,prefix+'_'+target+'1' if cc else finger+'_01_'+side,
                          prefix+'_'+target+'3' if cc else finger+'_03_'+side))
    for _,start,end in specs:assert start in bones and end in bones,(start,end)
    return specs

def rig(folder,name,mesh,cc=False):
    path=folder+'/'+name
    asset=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(name,folder,unreal.IKRigDefinition,unreal.IKRigDefinitionFactory())
    ctrl=unreal.IKRigController.get_controller(asset)
    assert ctrl.set_skeletal_mesh(mesh)
    assert ctrl.set_retarget_root('Pelvis' if cc else 'pelvis')
    assert ctrl.set_root_motion_bone('BoneRoot' if cc else 'root')
    specs=chain_specs({str(n) for n in mesh.skeleton.get_reference_pose().get_bone_names()},cc)
    existing={str(c.chain_name) for c in ctrl.get_retarget_chains()}
    for name,start,end in specs:
        if name not in existing:ctrl.add_retarget_chain(name,start,end,'None')
    eal.save_loaded_asset(asset)
    return asset,specs

for child in census['children']:
    identity=child['identity'];result={'identity':identity,'clips':[],'retargeters':[],'success':False}
    try:
        folder=candidate['folder'] if CANDIDATE else child.get('folder','/Game/Carnival/Characters/Children/'+identity)
        target=unreal.load_asset(child['mesh']);assert isinstance(target,unreal.SkeletalMesh)
        cc=identity=='BlackBoy';target_rig,target_specs=rig(folder+'/Retarget','IK_'+identity,target,cc)
        required=['Pelvis','Head','L_Hand','R_Hand','L_Foot','R_Foot'] if cc else ['pelvis','head','hand_l','hand_r','foot_l','foot_r']
        root='BoneRoot' if cc else 'root'
        evaluation=unreal.AnimPoseEvaluationOptions();evaluation.optional_skeletal_mesh=target
        evaluation.should_retarget=True;evaluation.incorporate_root_motion_into_pose=True
        for group,source_path,names in GROUPS:
            source=unreal.load_asset(source_path);assert isinstance(source,unreal.SkeletalMesh)
            source_rig,_=rig(folder+'/Retarget','IK_Source_'+group,source)
            path=folder+'/Retarget/RTG_'+group+'_To_'+identity
            retarget=unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset('RTG_'+group+'_To_'+identity,
                folder+'/Retarget',unreal.IKRetargeter,unreal.IKRetargetFactory())
            ctrl=unreal.IKRetargeterController.get_controller(retarget)
            ctrl.set_ik_rig(S,source_rig);ctrl.set_ik_rig(T,target_rig)
            ctrl.set_preview_mesh(S,source);ctrl.set_preview_mesh(T,target)
            if ctrl.get_num_retarget_ops()==0:ctrl.add_default_ops()
            ctrl.assign_ik_rig_to_all_ops(S,source_rig);ctrl.assign_ik_rig_to_all_ops(T,target_rig)
            ctrl.auto_map_chains(unreal.AutoMapChainType.EXACT,True)
            for i in range(ctrl.get_num_retarget_ops()):
                if str(ctrl.get_op_name(i)) in ('IK Chains','IK Solve','Run IK Rig'):
                    ctrl.set_retarget_op_enabled(i,False)
            pose_name='Child_Aligned_To_'+group
            if pose_name not in [str(n) for n in ctrl.get_retarget_poses(T)]:ctrl.create_retarget_pose(pose_name,T)
            ctrl.set_current_retarget_pose(pose_name,T);ctrl.reset_retarget_pose(pose_name,[],T)
            ctrl.auto_align_all_bones(T,unreal.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
            for name,_,_ in target_specs:assert str(ctrl.get_source_chain(name))==name,(identity,name,ctrl.get_source_chain(name))
            eal.save_loaded_asset(retarget)
            result['retargeters'].append(path)
            assets=[]
            for name in names:
                candidates=[a for a in census['animations'] if a['name']==name]
                assert len(candidates)==1,(name,candidates)
                clip=unreal.load_asset(candidates[0]['path'])
                assert clip.get_editor_property('skeleton')==source.skeleton,(name,source_path)
                package=candidates[0]['path'].split('.')[0]
                data=list(registry.get_assets_by_package_name(package));assert len(data)==1
                destination=folder+'/Animations/Child_'+group+'_'+name
                if not eal.does_asset_exist(destination):assets.append(data[0])
            if assets:
                inputs=unreal.IKRetargetBatchOperationInputs()
                inputs.assets_to_retarget=assets;inputs.source_mesh=source;inputs.target_mesh=target
                inputs.ik_retarget_asset=retarget;inputs.prefix='Child_'+group+'_'
                inputs.target_path=folder+'/Animations';inputs.include_referenced_assets=False
                inputs.overwrite_existing_files=False
                imported=unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
                assert len(imported)==len(assets),(len(imported),len(assets))
            for name in names:
                clip=unreal.load_asset(folder+'/Animations/Child_'+group+'_'+name)
                assert isinstance(clip,unreal.AnimSequence) and clip.get_editor_property('skeleton')==target.skeleton
                clip.set_editor_property('enable_root_motion',False);clip.set_editor_property('force_root_lock',True)
                clip.set_editor_property('root_motion_root_lock',unreal.RootMotionRootLock.ANIM_FIRST_FRAME)
                duration=clip.get_editor_property('sequence_length');assert duration>.1
                # This source run contains forward root translation even with
                # enable_root_motion=False. ForceRootLock is a playback setting;
                # pose evaluation still exposes that drift. Bake only the owned
                # root position track to its initial position for true in-place
                # locomotion; retain all rotations/scales and limb animation.
                key_count=unreal.AnimationLibrary.get_num_keys(clip)
                root_keys=[]
                for frame in range(key_count):
                    pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,duration*frame/max(key_count-1,1),evaluation)
                    root_keys.append(pose.get_bone_pose(root,unreal.AnimPoseSpaces.LOCAL))
                raw_root_drift=max(unreal.Vector.distance(tx.translation,root_keys[0].translation) for tx in root_keys)
                if raw_root_drift>=1:
                    controller=clip.get_editor_property('controller')
                    controller.open_bracket('Bake owned child locomotion root in place',False)
                    try:
                        assert controller.set_bone_track_keys(root,[root_keys[0].translation]*key_count,
                            [tx.rotation for tx in root_keys],[tx.scale3d for tx in root_keys],False)
                    finally:controller.close_bracket(False)
                samples=[]
                for fraction in (0,.25,.5,.75,1):
                    pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,duration*fraction,evaluation)
                    transforms={str(n):pose.get_bone_pose(n,unreal.AnimPoseSpaces.WORLD) for n in pose.get_bone_names()}
                    assert all(n in transforms for n in required+[root])
                    for bone,tx in transforms.items():
                        assert all(math.isfinite(v) for v in tx.translation.to_tuple()+tx.scale3d.to_tuple()),(identity,name,bone)
                        assert min(tx.scale3d.to_tuple())>.001 and max(tx.scale3d.to_tuple())<10,(identity,name,bone,str(tx))
                    samples.append({'fraction':fraction,'positions_cm':{n:transforms[n].translation.to_tuple() for n in required+[root]}})
                root_positions=[s['positions_cm'][root] for s in samples]
                assert max(math.dist(p,root_positions[0]) for p in root_positions)<1,(identity,name,root_positions)
                eal.save_loaded_asset(clip)
                result['clips'].append({'asset':clip.get_path_name(),'source_name':name,'group':group,
                    'seconds':duration,'sampled_bone_count':len(transforms),'samples':samples,
                    'root_drift_before_in_place_bake_cm':raw_root_drift,
                    'requires_ride_pose_fitting':group=='SeatedSource'})
        result['success']=len(result['clips'])==6
    except Exception:
        REPORT['errors'].append(identity+': '+traceback.format_exc())
    REPORT['children'].append(result)
    (OUT/REPORT_FILE).write_text(json.dumps(REPORT,indent=2))
REPORT['success']=len(REPORT['children'])==(1 if CANDIDATE else 4) and all(c['success'] for c in REPORT['children']) and not REPORT['errors']
(OUT/REPORT_FILE).write_text(json.dumps(REPORT,indent=2))
