"""Match local mount/dismount seated endpoints to the fitted riding pose."""
import json
import math
from pathlib import Path
import unreal

base='/Game/Carnival/Vehicles/Motorcycle/Fitted'
api=unreal.AnimPoseExtensions
options=unreal.AnimPoseEvaluationOptions()
options.should_retarget=True
options.optional_skeletal_mesh=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
idle=unreal.load_asset(base+'/Bike_Fitted_Idle')
assert idle
idle_pose=api.get_anim_pose_at_time(idle,0.,options)
names=api.get_bone_names(idle_pose)
local=unreal.AnimPoseSpaces.LOCAL
world=unreal.AnimPoseSpaces.WORLD

def blend_rotation(a,b,w):
    a=list(a.to_tuple()); b=list(b.to_tuple())
    if sum(x*y for x,y in zip(a,b))<0: b=[-x for x in b]
    q=[x*(1-w)+y*w for x,y in zip(a,b)]
    scale=math.sqrt(sum(x*x for x in q))
    return unreal.Quat(*(x/scale for x in q))

def blend_vector(a,b,w):
    return unreal.Vector(*(x*(1-w)+y*w for x,y in zip(a.to_tuple(),b.to_tuple())))

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def unit(a): return mul(a,1/max(norm(a),1e-8))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def qm(a,b): return (*add(add(mul(a[:3],b[3]),mul(b[:3],a[3])),cross(a[:3],b[:3])),a[3]*b[3]-dot(a[:3],b[:3]))
def qi(q): return (-q[0],-q[1],-q[2],q[3])
def between(a,b):
    a,b=unit(a),unit(b)
    return unit((*cross(a,b),1+dot(a,b)))
def smooth(x):
    x=max(0.,min(1.,x))
    return x*x*(3.-2.*x)

report=[]
for name in ['Mount_Left','Mount_Right','Dismount_Left','Dismount_Right']:
    source=unreal.load_asset(base+'/Bike_AS_'+name)
    assert source
    destination=base+'/Bike_Fitted_'+name
    clip=unreal.load_asset(destination) if unreal.EditorAssetLibrary.does_asset_exist(destination) else unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name(),destination)
    assert clip
    count=unreal.AnimationLibrary.get_num_keys(source)
    length=source.get_play_length()
    tracks={str(n):[[],[],[]] for n in names}
    mounting=name.startswith('Mount_')
    body_source=source if mounting else unreal.load_asset(base+'/Bike_AS_Mount_'+name.rsplit('_',1)[1])
    for frame in range(count):
        t=length*frame/max(count-1,1)
        source_time=t if mounting else body_source.get_play_length()*(1.-t/length)
        pose=api.get_anim_pose_at_time(body_source,source_time,options)
        # Preserve the step-over movement, then smoothly settle at the seat.
        # Dismount starts from exactly that same fitted seated configuration.
        w=max(0.,min(1.,(t/length-.6)/.4 if mounting else 1.-t/length/.4))
        w=w*w*(3.-2.*w)
        for bone in names:
            a=api.get_bone_pose(pose,bone,local)
            b=api.get_bone_pose(idle_pose,bone,local)
            positions,rotations,scales=tracks[str(bone)]
            positions.append(blend_vector(a.translation,b.translation,w))
            if str(bone)=='pelvis':
                progress=t/length if mounting else 1.-t/length
                positions[-1].z += 20.*smooth(progress/.25)*smooth((1.-progress)/.3)
                if name.endswith('Right'):
                    positions[-1].x -= 25.*smooth((progress-.05)/.15)*smooth((.65-progress)/.25)
            rotations.append(blend_rotation(a.rotation,b.rotation,w))
            scales.append(blend_vector(a.scale3d,b.scale3d,w))
    controller=clip.get_editor_property('controller')
    existing_tracks={str(n) for n in unreal.AnimationLibrary.get_animation_track_names(clip)}
    controller.open_bracket('Match motorcycle transition to fitted seat pose',False)
    try:
        for bone,(positions,rotations,scales) in tracks.items():
            # Some optional skeleton bones do not have tracks in the source.
            if bone not in existing_tracks:
                controller.add_bone_track(bone,False)
            assert controller.set_bone_track_keys(bone,positions,rotations,scales,False),bone
    finally:
        controller.close_bracket(False)
    # Route ankles around/over the rear seat, then solve the knees. Blending
    # source joint angles directly had sent the crossing shin through the tank.
    leg_tracks={}
    leg_reach=[]
    side_sign=-1 if name.endswith('Left') else 1
    def mesh_point(p): return (-p[1],p[0],p[2]-2.195294)
    def path_point(points,p):
        for (t0,a),(t1,b) in zip(points,points[1:]):
            if p<=t1:
                w=smooth((p-t0)/(t1-t0))
                return add(mul(a,1-w),mul(b,w))
        return points[-1][1]
    stand_pose=api.get_anim_pose_at_time(body_source,0.,options)
    for frame in range(count):
        t=length*frame/max(count-1,1)
        progress=t/length if mounting else 1.-t/length
        pose=api.get_anim_pose_at_time(clip,t,options)
        for side in ['l','r']:
            near=(side=='l')==name.endswith('Left')
            bones=['thigh_'+side,'calf_'+side,'foot_'+side]
            transforms=[api.get_bone_pose(pose,b,world) for b in bones]
            a,b,c=[tuple(tf.translation.to_tuple()) for tf in transforms]
            stand=tuple(api.get_bone_pose(stand_pose,bones[2],world).translation.to_tuple())
            seated=api.get_bone_pose(idle_pose,bones[2],world)
            points=([(0.,stand),(.3,mesh_point((-8,side_sign*30,46))),
                     (.7,mesh_point((-8,side_sign*30,46))),(1.,tuple(seated.translation.to_tuple()))] if near else
                    [(0.,stand),(.25,mesh_point((-45,side_sign*55,65))),
                     (.45,mesh_point((-65,side_sign*25,125))),(.65,mesh_point((-60,-side_sign*35,120))),
                     (.8,mesh_point((-25,-side_sign*40,75))),(1.,tuple(seated.translation.to_tuple()))])
            desired=path_point(points,progress)
            l1,l2=norm(sub(b,a)),norm(sub(c,b))
            delta=sub(desired,a); distance=norm(delta); axis=unit(delta)
            reach=max(abs(l1-l2)+.01,min(distance,l1+l2-.01))
            target=add(a,mul(axis,reach))
            # Knees point forward and outward while the crossing ankle rises.
            outward=-1 if side=='l' else 1
            pole_hint=mesh_point((55,outward*70,100))
            pole=unit(sub(sub(pole_hint,a),mul(axis,dot(sub(pole_hint,a),axis))))
            x=(l1*l1-l2*l2+reach*reach)/(2*reach)
            joint=add(add(a,mul(axis,x)),mul(pole,math.sqrt(max(0,l1*l1-x*x))))
            endpoint=smooth((progress-.8)/.2)
            rotation=blend_rotation(transforms[2].rotation,seated.rotation,smooth(progress/(.25 if near else .4)))
            rotations=[qm(between(sub(b,a),sub(joint,a)),tuple(transforms[0].rotation.to_tuple())),
                       qm(between(sub(c,b),sub(target,joint)),tuple(transforms[1].rotation.to_tuple())),tuple(rotation.to_tuple())]
            parents=[tuple(api.get_bone_pose(pose,'pelvis',world).rotation.to_tuple()),rotations[0],rotations[1]]
            for bone,rotation,parent in zip(bones,rotations,parents):
                q=unreal.Quat(*unit(qm(qi(parent),rotation)))
                # Preserve exact fitted seated knee attitude at the endpoint.
                fitted=api.get_bone_pose(idle_pose,bone,local).rotation
                leg_tracks.setdefault(bone,[]).append(blend_rotation(q,fitted,endpoint))
            leg_reach.append({'frame':frame,'side':side,'shortfall_cm':max(0.,distance-reach)})
    controller.open_bracket('Route motorcycle step-over legs around chassis',False)
    try:
        for bone,rotations in leg_tracks.items():
            assert controller.set_bone_track_keys(bone,tracks[bone][0],rotations,tracks[bone][2],False)
    finally:
        controller.close_bracket(False)
    # Solve the hands after the body blend so contacts are in bike space,
    # independent of the changing shoulder position during the step-over.
    arm_tracks={}
    contact_samples=[]
    for frame in range(count):
        t=length*frame/max(count-1,1)
        pose=api.get_anim_pose_at_time(clip,t,options)
        progress=t/length if mounting else 1.-t/length
        for side in ['l','r']:
            near=(side=='l')==name.endswith('Left')
            weight=smooth((progress-(.1 if near else .55))/(.35 if near else .3))
            if not mounting:
                weight=smooth(((.5 if near else .4)-t/length)/(.3 if near else .25))
            bones=['upperarm_'+side,'lowerarm_'+side,'hand_'+side]
            transforms=[api.get_bone_pose(pose,b,world) for b in bones]
            a,b,c=[tuple(tf.translation.to_tuple()) for tf in transforms]
            grip=api.get_bone_pose(idle_pose,bones[2],world)
            desired=add(mul(c,1-weight),mul(tuple(grip.translation.to_tuple()),weight))
            l1,l2=norm(sub(b,a)),norm(sub(c,b))
            delta=sub(desired,a); distance=norm(delta); axis=unit(delta)
            reach=max(abs(l1-l2)+.01,min(distance,l1+l2-.01))
            target=add(a,mul(axis,reach))
            pole=unit(sub(sub(b,a),mul(axis,dot(sub(b,a),axis))))
            x=(l1*l1-l2*l2+reach*reach)/(2*reach)
            joint=add(add(a,mul(axis,x)),mul(pole,math.sqrt(max(0,l1*l1-x*x))))
            rotations=[qm(between(sub(b,a),sub(joint,a)),tuple(transforms[0].rotation.to_tuple())),
                       qm(between(sub(c,b),sub(target,joint)),tuple(transforms[1].rotation.to_tuple())),
                       tuple(blend_rotation(transforms[2].rotation,grip.rotation,weight).to_tuple())]
            parents=[tuple(api.get_bone_pose(pose,'clavicle_'+side,world).rotation.to_tuple()),rotations[0],rotations[1]]
            for bone,rotation,parent in zip(bones,rotations,parents):
                arm_tracks.setdefault(bone,[]).append(unreal.Quat(*unit(qm(qi(parent),rotation))))
            contact_samples.append({'frame':frame,'hand':side,'grip_weight':weight,
                                    'unreachable_cm':max(0.,distance-reach),'target_mesh':target})
    controller.open_bracket('Fit transition hand approach to handlebar grips',False)
    try:
        for bone,rotations in arm_tracks.items():
            assert controller.set_bone_track_keys(bone,tracks[bone][0],rotations,tracks[bone][2],False)
    finally:
        controller.close_bracket(False)
    clip.set_editor_property('enable_root_motion',False)
    clip.set_editor_property('force_root_lock',False)
    for curve in ['DisableLegIK','DisableHandIKRetargeting']:
        if not unreal.AnimationLibrary.does_curve_exist(clip,curve,unreal.RawCurveTrackTypes.RCT_FLOAT):
            unreal.AnimationLibrary.add_curve(clip,curve,unreal.RawCurveTrackTypes.RCT_FLOAT,False)
        unreal.AnimationLibrary.add_float_curve_keys(clip,curve,[0.,length],[1.,1.])
    assert unreal.EditorAssetLibrary.save_loaded_asset(clip,False)
    for sample in contact_samples:
        evaluated=api.get_anim_pose_at_time(clip,length*sample['frame']/max(count-1,1),options)
        actual=api.get_bone_pose(evaluated,'hand_'+sample['hand'],world).translation.to_tuple()
        sample['evaluated_error_cm']=norm(sub(actual,sample['target_mesh']))
        assert sample['evaluated_error_cm']<.1,sample
    seated=api.get_anim_pose_at_time(clip,length if mounting else 0.,options)
    errors={}
    for bone in ['pelvis','hand_l','hand_r','foot_l','foot_r']:
        a=api.get_bone_pose(seated,bone,world).translation
        b=api.get_bone_pose(idle_pose,bone,world).translation
        errors[bone]=math.sqrt(sum((x-y)**2 for x,y in zip(a.to_tuple(),b.to_tuple())))
    assert max(errors.values())<.1,errors
    report.append({'asset':destination,'keys':count,'seated_joint_errors_cm':errors,
                   'contact_samples':contact_samples,'leg_reach':leg_reach})
Path(r'F:\Carnival\Saved\DirtBike\Transition_Fitting.json').write_text(json.dumps(report,indent=2))
unreal.log('MOTORCYCLE_TRANSITION_FITTING_COMPLETE')
