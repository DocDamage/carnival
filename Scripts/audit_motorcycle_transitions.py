"""Sample existing transition clips against the actual rider mesh and seat."""
import json
from pathlib import Path
import unreal

root=Path(r'F:\Carnival')
mesh=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
options=unreal.AnimPoseEvaluationOptions()
options.optional_skeletal_mesh=mesh
options.should_retarget=True
options.evaluation_type=unreal.AnimDataEvalType.COMPRESSED
report={}
for prefix in ['/Game/Carnival/Vehicles/Motorcycle/Animations/AS_', '/Game/Carnival/Vehicles/Motorcycle/Fitted/Bike_AS_']:
    for name in ['Mount_Left','Mount_Right','Dismount_Left','Dismount_Right']:
        clip=unreal.load_asset(prefix+name)
        assert clip, prefix+name
        length=clip.get_play_length()
        samples=[]
        for fraction in [0,.25,.5,.75,1]:
            pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,length*fraction,options)
            bones={}
            for bone in ['root','pelvis','hand_l','hand_r','foot_l','foot_r']:
                transform=unreal.AnimPoseExtensions.get_bone_pose(pose,bone,unreal.AnimPoseSpaces.WORLD)
                p=transform.translation
                bones[bone]=[round(p.y,3),round(-p.x,3),round(p.z+2.195294,3)]
            samples.append({'fraction':fraction,'bones_bike_space':bones})
        report[clip.get_path_name()]={'length':length,'samples':samples}
out=root/'Saved/DirtBike/Transition_Pose_Audit.json'
out.write_text(json.dumps(report,indent=2))
unreal.log('MOTORCYCLE_TRANSITION_AUDIT_COMPLETE')
