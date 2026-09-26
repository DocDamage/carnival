"""Author and export original stiff-doll actions on the mobile rig in Blender."""
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler, Vector
from io_scene_fbx import export_fbx_bin

# Blender 4.5 writes current-pose bone Model defaults into an animation-only FBX.
# Without a skinned mesh/bind-pose block, importers can treat that pose as rest
# and subtract its offsets from the motion. Write actual rest transforms into
# Model defaults while leaving the exporter's evaluated animation bake intact.
# This wrapper lives only in this process; the installed exporter is unchanged.
_write_model = export_fbx_bin.fbx_data_object_elements


class ReferenceBone:
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def fbx_object_tx(self, scene_data, **kwargs):
        return self.wrapped.fbx_object_tx(scene_data, rest=True)


def write_reference_model(root, obj, scene_data):
    return _write_model(root, ReferenceBone(obj) if obj.is_bone else obj, scene_data)


export_fbx_bin.fbx_data_object_elements = write_reference_model

OUT = Path(r"F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Mobile")
QA = Path(r"F:\Carnival\Saved\HauntedDollMobile")
ANIMS = OUT / "Animations"
ANIMS.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT / "Possessed_Doll_Mobile_Rig.blend"))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.render.fps = 30
rig = bpy.data.objects["Doll_Mobile_Rig"]
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
rig.animation_data.action = None
for old in list(bpy.data.actions):
    bpy.data.actions.remove(old)

# A single skeletal mesh with two materials is easier to import into a game.
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.parent == rig]
bpy.ops.object.select_all(action="DESELECT")
for ob in meshes:
    ob.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects.get("Doll_Body_and_Dress") or bpy.data.objects["Possessed_Doll_Mobile"]
if len(meshes) > 1:
    bpy.ops.object.join()
mesh = bpy.context.object
mesh.name = "Possessed_Doll_Mobile"

defs = {b.name: {"head": list(b.head_local), "tail": list(b.tail_local), "parent": b.parent.name if b.parent else None}
        for b in rig.data.bones}


def update():
    rig.update_tag()
    bpy.context.view_layer.update()


def reset():
    for p in rig.pose.bones:
        p.rotation_euler = (0, 0, 0)
        p.location = (0, 0, 0)
        p.scale = (1, 1, 1)
    rig.pose.bones["root"]["Hand IK L"] = 0.0
    rig.pose.bones["root"]["Hand IK R"] = 0.0


def rotate(name, angles):
    pb = rig.pose.bones[name]
    m = pb.bone.matrix_local.to_3x3()
    r = Euler([math.radians(a) for a in angles], "XYZ").to_matrix()
    pb.rotation_euler = (m.inverted() @ r @ m).to_euler("XYZ")


def translate(name, vector):
    pb = rig.pose.bones[name]
    pb.location = pb.bone.matrix_local.to_3x3().inverted() @ Vector(vector)


def smooth(x):
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


def segment(t, points):
    if t <= points[0][0]:
        return points[0][1]
    for (ta, va), (tb, vb) in zip(points, points[1:]):
        if t <= tb:
            s = smooth((t - ta) / (tb - ta))
            return va + (vb - va) * s
    return points[-1][1]


def idle(t):
    u = t % 4.0
    yaw = segment(u, [(0, -4), (.85, -4), (.95, 9), (1.9, 9), (2.03, -10), (3.72, -10), (4, -4)])
    roll = segment(u, [(0, 6), (1.15, 6), (1.27, 11), (2.6, 11), (2.72, 4), (3.8, 4), (4, 6)])
    translate("pelvis", (.004 * math.sin(t * math.pi / 2), 0, -.028))
    rotate("head", (2, roll, yaw))
    rotate("spine_02", (2, .8 * math.sin(t * math.pi / 2), 0))
    rotate("lowerarm_l", (-5, 0, 2))
    rotate("lowerarm_r", (-3, 0, -2))
    rotate("hand_l", (0, 6, 0))
    rotate("hand_r", (0, -4, 0))


def gait(t, run=False, root_motion=False):
    period = .8 if run else 1.6
    duty = .42 if run else .62
    amplitude = .17 if run else .135
    lift = .14 if run else .058
    speed = (2 * amplitude) / (duty * period)
    phase = (t / period) % 1
    translate("root", (0, -speed * t if root_motion else 0, 0))
    translate("pelvis", (.006 * math.sin(2 * math.pi * phase), 0,
                         (-.055 if run else -.036) + (.02 if run else .006) * math.cos(4 * math.pi * phase)))
    for side, shift, sign in [("l", 0, 1), ("r", .5, -1)]:
        p = (phase + shift) % 1
        if p < duty:
            y = -amplitude + 2 * amplitude * p / duty
            z = 0
            pitch = 0
        else:
            s = (p - duty) / (1 - duty)
            y = amplitude - 2 * amplitude * smooth(s)
            z = lift * math.sin(math.pi * s) ** 1.25
            pitch = -10 * math.sin(math.pi * s)
        translate("CTRL_foot_IK_" + side, (0, y, z))
        rotate("CTRL_foot_IK_" + side, (pitch, 0, 0))
        rotate("upperarm_" + side, ((-19 if run else -8) + (11 if run else 5) * math.sin(2 * math.pi * (phase + shift)),
                                     -sign * 4, sign * 2))
        rotate("lowerarm_" + side, (-28 if run else -10, 0, sign * -4))
        rotate("hand_" + side, (0, sign * 7, 0))
        rotate("dress_front_" + side, ((4 if run else 2) * math.sin(2 * math.pi * (phase + shift)), 0, 0))
        rotate("dress_side_" + side, (0, sign * (2 if run else 1) * math.sin(2 * math.pi * (phase + shift)), 0))
    jerk = segment(phase, [(0, 0), (.20, 0), (.24, 7), (.40, 7), (.45, -3), (.75, -3), (.79, -6), (.95, -6), (1, 0)])
    rotate("head", (7 if run else 2, 5 + jerk, jerk * .5))
    rotate("spine_01", (5 if run else 1, 1.2 * math.sin(2 * math.pi * phase), 0))
    return speed


def scare(t):
    idle(0)
    anticipation = segment(t, [(0, 0), (.4, 0), (.7, 1), (.9, 0), (2.2, 0)])
    reach = segment(t, [(0, 0), (.65, 0), (.88, 1), (1.42, 1), (2.2, 0)])
    launch = smooth((t - .72) / .46)
    airborne = .72 < t < 1.18
    arc = .22 * math.sin(math.pi * (t - .72) / .46) if airborne else 0
    impact = segment(t, [(0, 0), (1.14, 0), (1.22, 1), (1.45, 0), (2.2, 0)])
    translate("root", (0, -.52 * launch, arc))
    translate("pelvis", (0, 0, -.028 - .085 * anticipation - .075 * impact))
    rotate("spine_01", (10 * reach, 0, 0))
    rotate("spine_02", (5 * reach, 0, 0))
    rotate("neck_01", (-8 * reach, 0, 0))
    tilt = segment(t, [(0, 6), (.55, 17), (.70, 17), (.79, -7), (1.5, -7), (2.2, 6)])
    rotate("head", (-3 * reach, tilt, 4 * (1 - reach)))
    for side, sign in [("l", 1), ("r", -1)]:
        rotate("upperarm_" + side, (-57 * reach, -sign * 7 * reach, 0))
        rotate("lowerarm_" + side, (-27 * reach - 5, 0, -sign * 9 * reach))
        rotate("hand_" + side, (-8 * reach, -sign * 10 * reach, 0))
        translate("CTRL_foot_IK_" + side, (0, 0, .06 * math.sin(math.pi * (t - .72) / .46) if airborne else 0))
        rotate("dress_front_" + side, (-5 * reach, 0, 0))


def jump(t):
    idle(0)
    prep = segment(t, [(0, 0), (.28, 1), (.38, 0), (1.4, 0)])
    impact = segment(t, [(0, 0), (.94, 0), (1.04, 1), (1.26, 0), (1.4, 0)])
    arc = .28 * math.sin(math.pi * (t - .38) / .60) if .38 < t < .98 else 0
    translate("root", (0, 0, arc))
    translate("pelvis", (0, 0, -.028 - .09 * prep - .09 * impact))
    for side, sign in [("l", 1), ("r", -1)]:
        rotate("upperarm_" + side, (-25 * arc / .28 + 8 * prep, -sign * 5 * arc / .28, 0))
        translate("CTRL_foot_IK_" + side, (0, 0, arc * .18))


def head_snap(t):
    idle(0)
    rotate("head", (segment(t, [(0, 0), (.55, 0), (.63, -7), (1.2, -7), (2, 0)]),
                    segment(t, [(0, 6), (.45, 16), (.60, 16), (.67, -13), (1.35, -13), (2, 6)]),
                    segment(t, [(0, -4), (.45, -18), (.59, -18), (.67, 22), (1.35, 22), (2, -4)])))


def reach(t):
    idle(0)
    s = segment(t, [(0, 0), (.35, 0), (.55, .6), (.95, 1), (1.45, 1), (2.4, 0)])
    rotate("upperarm_l", (-43 * s, -8 * s, 0))
    rotate("lowerarm_l", (-5 - 30 * s, 0, -8 * s))
    rotate("hand_l", (-6 * s, 6 - 16 * s, 0))
    rotate("head", (2, 6 + 8 * s, -4))
    rotate("spine_02", (2 + 4 * s, 0, 0))


def clear_skirt():
    """Bake the skirt's six bones to follow knee clearance, also in FBX."""
    update()
    for side in ["l", "r"]:
        thigh = rig.pose.bones["thigh_" + side]
        direction = thigh.tail - thigh.head
        pitch = math.degrees(math.atan2(direction.y, -direction.z))
        front = min(0, pitch + 4)
        back = max(0, pitch + 4)
        rotate("dress_front_" + side, (front * .85, 0, 0))
        rotate("dress_back_" + side, (back * .65, 0, 0))
        rotate("dress_side_" + side, (pitch * .25, 0, 0))


specs = [
    ("Doll_Idle_Possessed_Loop", 120, True, "in_place", idle),
    ("Doll_Walk_Twitchy_InPlace", 48, True, "in_place", lambda t: gait(t)),
    ("Doll_Walk_Twitchy_RootMotion", 48, True, "root_motion", lambda t: gait(t, root_motion=True)),
    ("Doll_Run_Twitchy_InPlace", 24, True, "in_place", lambda t: gait(t, run=True)),
    ("Doll_Run_Twitchy_RootMotion", 24, True, "root_motion", lambda t: gait(t, run=True, root_motion=True)),
    ("Doll_Jumpscare_Lunge", 66, False, "root_motion", scare),
    ("Doll_Jump_InPlace", 42, False, "root_motion_vertical", jump),
    ("Doll_Head_Snap", 60, False, "in_place", head_snap),
    ("Doll_Reach_Grab", 72, False, "in_place", reach),
]

# Export the reference mesh BEFORE any action, with FK-compatible leg bind pose.
reset()
update()
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
fbx_settings = dict(use_selection=True, object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
                    use_armature_deform_only=True, axis_forward="-Y", axis_up="Z",
                    apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", path_mode="RELATIVE")
bpy.ops.export_scene.fbx(filepath=str(OUT / "Possessed_Doll_Mobile.fbx"), bake_anim=False, **fbx_settings)
bpy.ops.export_scene.gltf(filepath=str(OUT / "Possessed_Doll_Mobile.glb"), export_format="GLB",
                          use_selection=True, export_animations=False, export_skins=True, export_def_bones=True)
mesh.select_set(False)

manifest = []
pose_checks = []
for name, intervals, loop, motion, pose in specs:
    rig.animation_data.action = None
    reset()
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data.action = action
    scene.frame_start = 1
    scene.frame_end = intervals + 1
    max_error = 0.0
    for i in range(intervals + 1):
        # Avoid accumulating the previous frame's pose when evaluating constraints.
        reset()
        pose(i / 30)
        clear_skirt()
        update()
        for side in ["l", "r"]:
            error = (rig.pose.bones["calf_" + side].tail - rig.pose.bones["CTRL_foot_IK_" + side].head).length
            max_error = max(max_error, error)
        for pb in rig.pose.bones:
            pb.keyframe_insert(data_path="rotation_euler", frame=i + 1, group=pb.name)
            pb.keyframe_insert(data_path="location", frame=i + 1, group=pb.name)
    # Samples are baked per frame; linear interpolation avoids overshoot on snaps.
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = "LINEAR"
    scene.frame_set(1)
    start = rig.pose.bones["root"].matrix.translation.copy()
    scene.frame_set(intervals + 1)
    finish = rig.pose.bones["root"].matrix.translation.copy()
    delta = finish - start
    bpy.ops.export_scene.fbx(filepath=str(ANIMS / (name + ".fbx")), bake_anim=True,
                              bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                              bake_anim_simplify_factor=0, **fbx_settings)
    manifest.append({"name": name, "fps": 30, "frames": [1, intervals + 1], "duration_seconds": intervals / 30,
                     "loop": loop, "motion": motion, "root_displacement_m": list(delta),
                     "max_leg_IK_target_error_m": max_error,
                     "nominal_speed_cm_s": float(abs(delta.y) / (intervals / 30) * 100) if motion == "root_motion" and loop else None})
    assert max_error < .005, (name, max_error)

# Concrete pose samples, including the hard extension in the jump scare.
samples = [("Doll_Idle_Possessed_Loop", 1), ("Doll_Walk_Twitchy_InPlace", 10),
           ("Doll_Run_Twitchy_InPlace", 7), ("Doll_Jumpscare_Lunge", 30),
           ("Doll_Jump_InPlace", 22), ("Doll_Head_Snap", 21), ("Doll_Reach_Grab", 34)]
camera = scene.camera
stage = bpy.data.collections["PREVIEW | Cameras and lighting"]
stage.hide_viewport = False
base_camera = camera.location.copy()
for name, frame in samples:
    rig.animation_data.action = bpy.data.actions[name]
    scene.frame_set(frame)
    move = rig.pose.bones["root"].matrix.translation - rig.data.bones["root"].head_local
    camera.location = base_camera + move
    scene.render.filepath = str(OUT / "Previews" / (name + ".png"))
    bpy.ops.render.render(write_still=True)
camera.location = base_camera
stage.hide_viewport = True
rig.animation_data.action = bpy.data.actions["Doll_Idle_Possessed_Loop"]
scene.frame_start = 1
scene.frame_end = 121
scene.frame_set(1)
for bone in rig.data.bones:
    bone.select = False
rig.data.bones.active = rig.data.bones["head"]
rig.data.bones["head"].select = True
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
for area in bpy.context.screen.areas:
    if area.type == "VIEW_3D":
        area.spaces.active.region_3d.view_distance = 2.3
        area.spaces.active.region_3d.view_location = (0, .20, .74)
        area.spaces.active.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
        area.spaces.active.region_3d.view_perspective = "ORTHO"
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "Possessed_Doll_Mobile_Rig.blend"))
(OUT / "Animation_Manifest.json").write_text(json.dumps(manifest, indent=2))
(QA / "mobile_bone_defs.json").write_text(json.dumps(defs, indent=2))
print("MOBILE_ANIMATIONS_COMPLETE", json.dumps(manifest))
