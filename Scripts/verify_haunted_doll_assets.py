"""Reload all deliverables, verify skeletons/poses, and retain a concise report."""
import json, math
from pathlib import Path
import unreal
BASE='/Game/Carnival/Characters/PossessedDoll'
OUT=Path(r'F:\Carnival\Saved\HauntedDollIntegration')
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.wait_for_completion()
mesh=unreal.load_asset(BASE+'/SK_Doll');skeleton=mesh.skeleton
ref=skeleton.get_reference_pose();bones=[str(n) for n in ref.get_bone_names()]
assert len(bones)==26 and bones[0]=='root'
assets=[a for a in registry.get_assets_by_path(BASE+'/Animations',True) if str(a.asset_class_path.asset_name)=='AnimSequence']
assert len(assets)==31,len(assets)
options=unreal.AnimPoseEvaluationOptions();options.optional_skeletal_mesh=mesh
options.incorporate_root_motion_into_pose=True
report={'mesh':mesh.get_path_name(),'bones':bones,'animations':[]}
for data in assets:
    animation=data.get_asset()
    assert animation.get_editor_property('skeleton')==skeleton
    length=animation.get_editor_property('sequence_length')
    assert length>0
    max_scale_error=0
    for fraction in [0,.25,.5,.75,1]:
        pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(animation,length*fraction,options)
        for bone in bones:
            tx=pose.get_bone_pose(bone,unreal.AnimPoseSpaces.WORLD)
            assert all(math.isfinite(v) for v in [tx.translation.x,tx.translation.y,tx.translation.z,tx.rotation.x,tx.rotation.y,tx.rotation.z,tx.rotation.w])
            max_scale_error=max(max_scale_error,max(abs(v-1) for v in [tx.scale3d.x,tx.scale3d.y,tx.scale3d.z]))
    assert max_scale_error<.002,(animation.get_name(),max_scale_error)
    report['animations'].append({'name':animation.get_name(),'seconds':length,'sampled_poses':5,'max_scale_error':max_scale_error})
bp=unreal.load_asset(BASE+'/BP_PossessedDoll')
cdo=unreal.get_default_object(bp.generated_class())
assert cdo.get_component_by_class(unreal.SkeletalMeshComponent).get_skeletal_mesh_asset()==mesh
for field in ['idle_animation','walk_animation','run_animation','notice_animation','scare_animation','reach_animation','jump_animation','ramster_idle_animation','scare_sound']:
    assert cdo.get_editor_property(field),field
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
dolls=[a for a in eas.get_all_level_actors() if 'Carnival.HauntedDoll.MainEncounter' in [str(t) for t in a.tags]]
assert len(dolls)==1
report['placed_actor']=dolls[0].get_path_name()
report['placed_location']=str(dolls[0].get_actor_location())
assert abs(dolls[0].get_actor_rotation().pitch)<.01 and abs(dolls[0].get_actor_rotation().roll)<.01,str(dolls[0].get_actor_rotation())
report['placed_rotation']=str(dolls[0].get_actor_rotation())
assert dolls[0].get_component_by_class(unreal.SkeletalMeshComponent).get_skeletal_mesh_asset()==mesh
(OUT/'Final_Asset_Validation.json').write_text(json.dumps(report,indent=2))
unreal.log_warning('DOLL_ASSET_VALIDATION_COMPLETE 31 clips / 26 bones / 155 sampled poses')
