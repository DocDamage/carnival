"""Export both leg chains throughout candidate transitions at 120 Hz."""
import json
import math
from pathlib import Path
import unreal

options=unreal.AnimPoseEvaluationOptions()
options.optional_skeletal_mesh=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
options.should_retarget=True
options.evaluation_type=unreal.AnimDataEvalType.COMPRESSED
report={}
for name in ['Mount_Left','Mount_Right','Dismount_Left','Dismount_Right',
             'Staged_Dismount_Left','Staged_Dismount_Right','Rear_Staged_Dismount_Left','Rear_Staged_Dismount_Right']:
    staged='Staged_' in name
    asset='Bike_Staged_Dismount_'+name.rsplit('_',1)[1] if staged else 'Bike_Fitted_'+name
    clip=unreal.load_asset('/Game/Carnival/Vehicles/Motorcycle/Fitted/'+asset)
    assert clip
    length=clip.get_play_length()
    count=math.ceil(length*120)
    end_pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,length,options)
    end_offset=[unreal.AnimPoseExtensions.get_curve_weight(end_pose,'BikeExit'+axis) for axis in 'XYZ'] if staged else [0,0,0]
    samples=[]
    for frame in range(count+1):
        time=length*frame/count
        pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,time,options)
        progress=unreal.AnimPoseExtensions.get_curve_weight(pose,'BikeExitProgress') if staged else 0.
        destination=(-70 if name.startswith('Rear_') else 0.,-120 if name.endswith('Left') else 120,-.195294)
        warp=unreal.AnimPoseExtensions.get_curve_weight(pose,'BikeExitWarp') if staged else 0.
        authored=[unreal.AnimPoseExtensions.get_curve_weight(pose,'BikeExit'+axis) for axis in 'XYZ'] if staged else [0,0,0]
        offset=tuple(a+(d-e)*warp for a,d,e in zip(authored,destination,end_offset))
        bones={}
        for side in ['l','r']:
            for part in ['thigh','calf','foot','ball']:
                bone=part+'_'+side
                p=unreal.AnimPoseExtensions.get_bone_pose(pose,bone,unreal.AnimPoseSpaces.WORLD).translation
                bones[bone]=[p.y+offset[0],-p.x+offset[1],p.z+2.195294+offset[2]]
        samples.append({'time':time,'fraction':frame/count,'exit_progress':progress,'actor_offset':offset,'bones':bones})
    if staged:
        assert abs(samples[0]['exit_progress'])<.001 and abs(samples[-1]['exit_progress']-1.)<.001,name
    report[name]=samples
Path(r'F:\Carnival\Saved\DirtBike\Transition_Leg_Samples.json').write_text(json.dumps(report))
unreal.log('MOTORCYCLE_LEG_SAMPLES_COMPLETE')
