"""Render installed in-place clips along the checked flat-ground exit path."""
from pathlib import Path
import runpy
import unreal

base='/Game/Carnival/Vehicles/Motorcycle/Fitted/Bike_Staged_Dismount_'
config={'show_rider':True,'clip':base+'Left','times':[],'clips':[],'rider_positions':[],'shots':[],
        'report':'StagedDismount_Capture_Report.json',
        'scope':'Dense rendered samples of installed skinned dismount clips on the 120 cm flat exit path; time-sampled frames do not replace continuous runtime acceptance.'}
options=unreal.AnimPoseEvaluationOptions()
fractions=(0.0,.1,.2,.3,.4,.5,.6,.7,.8,.9,.925,.95,.975,1.0)
for side,sign in [('Left',-1),('Right',1)]:
    clip=unreal.load_asset(base+side)
    end_pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,clip.get_play_length(),options)
    names=('BikeExitX','BikeExitY','BikeExitZ')
    end=tuple(unreal.AnimPoseExtensions.get_curve_weight(end_pose,name) for name in names)
    destination=(0,sign*120,-.195294)
    for fraction in fractions:
        label=f'{int(round(fraction*1000)):04d}'
        t=clip.get_play_length()*fraction
        pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,t,options)
        progress=unreal.AnimPoseExtensions.get_curve_weight(pose,'BikeExitProgress')
        if fraction==1.: assert progress>.999
        config['times'].append(t); config['clips'].append(base+side)
        offset=tuple(unreal.AnimPoseExtensions.get_curve_weight(pose,name) for name in names)
        warp=unreal.AnimPoseExtensions.get_curve_weight(pose,'BikeExitWarp')
        position=tuple(offset[i]+(destination[i]-end[i])*warp for i in range(3))
        config['rider_positions'].append((position[0],position[1],98.195294+position[2]))
        config['shots'].append((f'StagedDismount_{side}_{label}',(140,sign*500,170),(0,sign*45,82)))
runpy.run_path(str(Path(__file__).with_name('preview_motorcycle_assembly.py')),init_globals={'PREVIEW_CONFIG':config})
