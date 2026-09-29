"""Read the riding pose evaluated with the player's actual skeletal proportions."""
import json
from pathlib import Path
import unreal
clip=unreal.load_asset('/Game/Carnival/Vehicles/Motorcycle/Fitted/Bike_AS_Idle_Riding')
mesh=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
options=unreal.AnimPoseEvaluationOptions()
options.optional_skeletal_mesh=mesh
options.should_retarget=True
options.evaluation_type=unreal.AnimDataEvalType.COMPRESSED
pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,.75,options)
out={}
for name in ['pelvis','clavicle_l','upperarm_l','lowerarm_l','hand_l','clavicle_r','upperarm_r','lowerarm_r','hand_r','thigh_l','calf_l','foot_l','ball_l','thigh_r','calf_r','foot_r','ball_r']:
    t=unreal.AnimPoseExtensions.get_bone_pose(pose,name,unreal.AnimPoseSpaces.WORLD)
    p=t.translation
    out[name]={'mesh':list(p.to_tuple()),'bike':[p.y,-p.x,p.z+2.195294]}
out['controller_api']=[x for x in dir(clip) if 'controller' in x or 'model' in x]
out['quat_api']=[x for x in dir(unreal.Quat) if any(y in x for y in ['find','inverse','multiply','rotate'])]
Path(r'F:\Carnival\Saved\DirtBike\Rider_Pose_Sample.json').write_text(json.dumps(out,indent=2))
