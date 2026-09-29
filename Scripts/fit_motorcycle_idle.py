"""Bake two-bone limb fitting into a local copy; preserve supplied animation assets."""
import json
import math
from pathlib import Path
import unreal

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def unit(a): return mul(a,1/max(norm(a),1e-8))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def qt(q): return (q.x,q.y,q.z,q.w)
def qm(a,b):
    v=add(add(mul(a[:3],b[3]),mul(b[:3],a[3])),cross(a[:3],b[:3]))
    return (*v,a[3]*b[3]-dot(a[:3],b[:3]))
def qi(q): return (-q[0],-q[1],-q[2],q[3])
def between(a,b):
    a,b=unit(a),unit(b)
    q=(*cross(a,b),1+dot(a,b))
    assert norm(q)>.001, 'Unexpected opposite limb vectors'
    return unit(q)
def mesh_point(bike): return (-bike[1],bike[0],bike[2]-2.195294)

base='/Game/Carnival/Vehicles/Motorcycle/Fitted'
source=unreal.load_asset(base+'/Bike_AS_Idle_Riding')
dest=base+'/Bike_Fitted_Idle'
assert source
# Always derive from the untouched retargeted clip, never accumulate fitting.
clip=unreal.load_asset(dest) if unreal.EditorAssetLibrary.does_asset_exist(dest) else unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name(),dest)
assert clip
options=unreal.AnimPoseEvaluationOptions()
options.should_retarget=True
options.optional_skeletal_mesh=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
api=unreal.AnimPoseExtensions
space=unreal.AnimPoseSpaces.WORLD
count=unreal.AnimationLibrary.get_num_keys(source)
length=unreal.AnimationLibrary.get_sequence_length(source)
tracks={}; positions_by_bone={}; scales_by_bone={}; targets={}; diagnostics=[]
for side,sign in [('l',-1),('r',1)]:
    targets['hand_'+side]=(34,sign*39,128)
    targets['foot_'+side]=(-8,sign*25,46)
for frame in range(count):
    pose=api.get_anim_pose_at_time(source,length*frame/max(count-1,1),options)
    def transform(n): return api.get_bone_pose(pose,n,space)
    def point(n): return tuple(transform(n).translation.to_tuple())
    for side in ['l','r']:
        for upper,lower,end,parent in [('upperarm','lowerarm','hand','clavicle_'+side),('thigh','calf','foot','pelvis')]:
            names=[n+'_'+side for n in [upper,lower,end]]
            a,b,c=[point(n) for n in names]
            target=mesh_point(targets[names[2]])
            l1,l2=norm(sub(b,a)),norm(sub(c,b))
            delta=sub(target,a); distance=norm(delta)
            assert abs(l1-l2)+.01<distance<l1+l2-.01,(names,distance,l1+l2)
            axis=unit(delta)
            pole=unit(sub(sub(b,a),mul(axis,dot(sub(b,a),axis))))
            x=(l1*l1-l2*l2+distance*distance)/(2*distance)
            joint=add(add(a,mul(axis,x)),mul(pole,math.sqrt(max(0,l1*l1-x*x))))
            world=[qm(between(sub(b,a),sub(joint,a)),qt(transform(names[0]).rotation)),
                   qm(between(sub(c,b),sub(target,joint)),qt(transform(names[1]).rotation)),
                   qt(transform(names[2]).rotation)]
            if end=='foot':
                # Level the forefoot above the peg while retaining the ankle's twist.
                world[2]=qm(between(sub(point('ball_'+side),c),(0,16,-5)),world[2])
            parents=[qt(transform(parent).rotation),world[0],world[1]]
            for name,w,p in zip(names,world,parents):
                q=unit(qm(qi(p),w))
                tracks.setdefault(name,[]).append(unreal.Quat(*q))
                local=api.get_bone_pose(pose,name,unreal.AnimPoseSpaces.LOCAL)
                positions_by_bone.setdefault(name,[]).append(local.translation)
                scales_by_bone.setdefault(name,[]).append(local.scale3d)
            if end=='foot':
                # Manny's post-slot foot rig targets the IK bones. Move these
                # alongside the fitted feet instead of leaving standing targets.
                ik='ik_foot_'+side
                parent_tf=transform('ik_foot_root')
                local_pos=parent_tf.inverse_transform_location(unreal.Vector(*target))
                local_rot=unit(qm(qi(qt(parent_tf.rotation)),world[2]))
                tracks.setdefault(ik,[]).append(unreal.Quat(*local_rot))
                positions_by_bone.setdefault(ik,[]).append(local_pos)
                scales_by_bone.setdefault(ik,[]).append(unreal.Vector(1,1,1))
controller=clip.get_editor_property('controller')
controller.open_bracket('Fit rider to assembled motorcycle',False)
try:
    for name,rotations in tracks.items():
        assert controller.set_bone_track_keys(name,positions_by_bone[name],rotations,scales_by_bone[name],False)
finally:
    controller.close_bracket(False)
for curve in ['DisableLegIK','DisableHandIKRetargeting']:
    if not unreal.AnimationLibrary.does_curve_exist(clip,curve,unreal.RawCurveTrackTypes.RCT_FLOAT):
        unreal.AnimationLibrary.add_curve(clip,curve,unreal.RawCurveTrackTypes.RCT_FLOAT,False)
    unreal.AnimationLibrary.add_float_curve_keys(clip,curve,[0.,length],[1.,1.])
unreal.EditorAssetLibrary.save_loaded_asset(clip,False)
for frame in [0,count//2,count-1]:
    pose=api.get_anim_pose_at_time(clip,length*frame/max(count-1,1),options)
    errors={name:norm(sub(tuple(api.get_bone_pose(pose,name,space).translation.to_tuple()),mesh_point(target))) for name,target in targets.items()}
    assert max(errors.values())<.1,errors
    diagnostics.append({'frame':frame,'joint_errors_cm':errors})
Path(r'F:\Carnival\Saved\DirtBike\Idle_Fitting.json').write_text(json.dumps({'asset':dest,'keys':count,'targets_bike_cm':targets,'samples':diagnostics},indent=2))
