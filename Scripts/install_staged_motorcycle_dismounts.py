"""Build in-place dismounts with an exit-progress curve for capsule staging."""
import json
import math
import shutil
from datetime import datetime
from pathlib import Path
import unreal

root=Path(r'F:\Carnival'); base='/Game/Carnival/Vehicles/Motorcycle/Fitted'
api=unreal.AnimPoseExtensions
options=unreal.AnimPoseEvaluationOptions()
options.should_retarget=True
options.optional_skeletal_mesh=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
backup=root/'Saved/DirtBike'/('StagedDismountBackup_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.uasset')
shutil.copy2(root/'Content/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.uasset',backup)
bp=unreal.load_asset('/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter')
cdo=unreal.get_default_object(bp.generated_class()); report={'backup':str(backup),'clips':[]}
for side in ['Left','Right']:
    source=unreal.load_asset(base+'/Bike_Fitted_Dismount_'+side)
    assert source
    path=base+'/Bike_Staged_Dismount_'+side
    clip=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name(),path)
    count=unreal.AnimationLibrary.get_num_keys(source); length=source.get_play_length()
    times=[length*i/(count-1) for i in range(count)]
    poses=[api.get_anim_pose_at_time(source,t,options) for t in times]
    roots=[api.get_bone_pose(p,'root',unreal.AnimPoseSpaces.LOCAL) for p in poses]
    assert all(abs(r.rotation.w)> .99999 for r in roots),'Root rotation requires explicit path conversion'
    controller=clip.get_editor_property('controller')
    controller.open_bracket('Remove root translation for staged dismount',False)
    try:
        # Copy all tracks on rerun so upstream fitting changes are preserved.
        existing={str(n) for n in unreal.AnimationLibrary.get_animation_track_names(clip)}
        for name in api.get_bone_names(poses[0]):
            if str(name) not in existing: controller.add_bone_track(name,False)
            transforms=[api.get_bone_pose(p,name,unreal.AnimPoseSpaces.LOCAL) for p in poses]
            positions=[unreal.Vector() if str(name)=='root' else t.translation for t in transforms]
            assert controller.set_bone_track_keys(name,positions,[t.rotation for t in transforms],[t.scale3d for t in transforms],False)
    finally: controller.close_bracket(False)
    for curve in ['BikeExitProgress','BikeExitWarp','BikeExitX','BikeExitY','BikeExitZ','DisableLegIK','DisableHandIKRetargeting']:
        if not unreal.AnimationLibrary.does_curve_exist(clip,curve,unreal.RawCurveTrackTypes.RCT_FLOAT):
            unreal.AnimationLibrary.add_curve(clip,curve,unreal.RawCurveTrackTypes.RCT_FLOAT,False)
    progress=[]; maximum=0.
    for r in roots:
        maximum=max(maximum,min(1.,max(0.,r.translation.x/roots[-1].translation.x)))
        progress.append(maximum)
    unreal.AnimationLibrary.add_float_curve_keys(clip,'BikeExitProgress',times,progress)
    warp=[]
    for t in times:
        w=max(0.,min(1.,(t/length-.7)/.3))
        warp.append(w*w*(3.-2.*w))
    unreal.AnimationLibrary.add_float_curve_keys(clip,'BikeExitWarp',times,warp)
    for curve,values in [('BikeExitX',[r.translation.y for r in roots]),
                         ('BikeExitY',[-r.translation.x for r in roots]),
                         ('BikeExitZ',[r.translation.z for r in roots])]:
        unreal.AnimationLibrary.add_float_curve_keys(clip,curve,times,values)
    for curve in ['DisableLegIK','DisableHandIKRetargeting']:
        unreal.AnimationLibrary.add_float_curve_keys(clip,curve,[0.,length],[1.,1.])
    clip.set_editor_property('enable_root_motion',False); clip.set_editor_property('force_root_lock',True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(clip,False)
    error=0.
    for i,t in enumerate(times):
        p=api.get_anim_pose_at_time(clip,t,options)
        for bone in ['pelvis','hand_l','hand_r','foot_l','foot_r']:
            a=api.get_bone_pose(p,bone,unreal.AnimPoseSpaces.WORLD).translation+roots[i].translation
            b=api.get_bone_pose(poses[i],bone,unreal.AnimPoseSpaces.WORLD).translation
            error=max(error,math.sqrt(sum((x-y)**2 for x,y in zip(a.to_tuple(),b.to_tuple()))))
    assert error<.1,error
    name='AM_Bike_Staged_Dismount_'+side
    montage=unreal.load_asset(base+'/'+name) if unreal.EditorAssetLibrary.does_asset_exist(base+'/'+name) else None
    if not montage:
        factory=unreal.AnimMontageFactory(); factory.set_editor_property('source_animation',clip)
        factory.set_editor_property('target_skeleton',clip.get_editor_property('skeleton'))
        montage=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,base,unreal.AnimMontage,factory)
    montage.set_editor_property('enable_auto_blend_out',False)
    assert unreal.EditorAssetLibrary.save_loaded_asset(montage,False)
    cdo.set_editor_property('dismount_'+side.lower()+'_montage',montage)
    report['clips'].append({'asset':path,'max_reconstruction_error_cm':error,'start_progress':progress[0],'end_progress':progress[-1]})
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
(root/'Saved/DirtBike/Staged_Dismount_Install.json').write_text(json.dumps(report,indent=2))
