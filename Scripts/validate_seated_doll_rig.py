"""Blender round-trip and deformation checks for the seated doll deliverables."""

import hashlib
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler, Vector
from mathutils.kdtree import KDTree

OUT = Path(r"F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Seated")
QA = Path(r"F:\Carnival\Saved\HauntedDollRig")
results = {}


def coordinates(mesh):
    bpy.context.view_layer.update()
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = evaluated.to_mesh()
    positions = [evaluated.matrix_world @ v.co for v in data.vertices]
    evaluated.to_mesh_clear()
    return positions


def geometry_error(reference, actual):
    tree = KDTree(len(reference))
    for i, point in enumerate(reference):
        tree.insert(point, i)
    tree.balance()
    errors = [tree.find(p)[2] for p in actual]
    return {"max_m": float(max(errors)), "p99_m": float(np.percentile(errors, 99))}


def rotate_world(rig, name, angles):
    pb = rig.pose.bones[name]
    rest = pb.bone.matrix_local.to_3x3()
    rot = Euler([math.radians(v) for v in angles], "XYZ").to_matrix()
    pb.rotation_euler = (rest.inverted() @ rot @ rest).to_euler("XYZ")


bpy.ops.wm.open_mainfile(filepath=str(OUT / "Possessed_Doll_Seated_Rig.blend"))
bpy.ops.object.mode_set(mode="OBJECT")
scene = bpy.context.scene
rig = bpy.data.objects["Doll_Seated_Rig"]
mesh = bpy.data.objects["Possessed_Doll"]
expected_bones = {b.name for b in rig.data.bones if b.use_deform}
scene.frame_set(1)
reference_rest = coordinates(mesh)
scene.frame_set(112)
reference_reach = coordinates(mesh)
scene.frame_set(1)
action = rig.animation_data.action
action_slot = rig.animation_data.action_slot
assert len(rig.data.bones) == 26
assert len(expected_bones) == 22
assert len([b for b in rig.data.bones if b.parent is None]) == 1
assert all(len(v.groups) <= 4 for v in mesh.data.vertices)
assert all(abs(sum(g.weight for g in v.groups) - 1) < 1e-5 for v in mesh.data.vertices)
results["skin"] = {"vertices": len(mesh.data.vertices), "controls_and_bones": 26,
                   "export_bones": 22, "all_vertices_weighted": True, "max_influences": 4}
results["packed_textures"] = [im.name for im in bpy.data.images if im.packed_file]
assert len(results["packed_textures"]) == 2

rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.rotation_euler = (0, 0, 0)
    pb.location = (0, 0, 0)

# Enable each IK arm and move its hand target inside the reachable workspace.
# This tests evaluated results, not merely the presence of constraints/drivers.
ik_results = []
for side in ["l", "r"]:
    master = rig.pose.bones["root"]
    master["Hand IK " + side.upper()] = 1.0
    rig.update_tag()
    bpy.context.view_layer.update()
    rest_error = geometry_error(reference_rest, coordinates(mesh))
    assert rest_error["max_m"] < .0001, (side, rest_error)
    target = rig.pose.bones["CTRL_hand_IK_" + side]
    delta = Vector((-.025 if side == "l" else .025, -.045, .045))
    target.location = target.bone.matrix_local.to_3x3().inverted() @ delta
    rig.update_tag()
    bpy.context.view_layer.update()
    endpoint_error = (rig.pose.bones["lowerarm_" + side].tail - target.head).length
    assert endpoint_error < .001, (side, endpoint_error)
    ik_results.append({"side": side, "rest_mesh_error_m": rest_error["max_m"],
                       "moved_target_error_m": endpoint_error})
    scene.render.filepath = str(OUT / "Previews" / ("IK_" + side + ".png"))
    bpy.ops.render.render(write_still=True)
    master["Hand IK " + side.upper()] = 0.0
    target.location = (0, 0, 0)
    rig.update_tag()
    bpy.context.view_layer.update()
results["hand_IK"] = ik_results

# Inspect the harder-to-see joins at the back of the neck and at the shoulders.
camera = scene.camera
target_point = Vector((0, .12, .53))
for view, location in [("back", (1.3, 3.4, .95)), ("side", (3.8, -.2, .9))]:
    for pb in rig.pose.bones:
        pb.rotation_euler = (0, 0, 0)
    rotate_world(rig, "head", (5, 16, -22))
    rotate_world(rig, "upperarm_l", (-35, -8, 0))
    rotate_world(rig, "lowerarm_l", (-20, 0, -8))
    bpy.context.view_layer.update()
    camera.location = location
    camera.rotation_euler = (target_point - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(OUT / "Previews" / ("QA_" + view + ".png"))
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.fbx(filepath=str(OUT / "Possessed_Doll_Seated.fbx"), use_anim=False)
fbx_mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
fbx_rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
assert {b.name for b in fbx_rig.data.bones} == expected_bones
assert not any(b.name.startswith("CTRL_") for b in fbx_rig.data.bones)
error = geometry_error(reference_rest, coordinates(fbx_mesh))
assert error["max_m"] < .0001, error
assert all(abs(sum(g.weight for g in v.groups) - 1) < 1e-5 for v in fbx_mesh.data.vertices)
results["FBX_bind_roundtrip"] = {"bones": len(fbx_rig.data.bones), "vertices": len(fbx_mesh.data.vertices), **error}
assert any(im.has_data and "Textures" in im.filepath for im in bpy.data.images), "FBX texture was not resolved"

before_objects = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(OUT / "Doll_Seated_Rig_Demo.fbx"), use_anim=True, anim_offset=0)
anim_rig = next(o for o in bpy.data.objects if o not in before_objects and o.type == "ARMATURE")
assert anim_rig.animation_data and anim_rig.animation_data.action
assert {b.name for b in anim_rig.data.bones} == expected_bones
fbx_rig.animation_data_create()
fbx_rig.animation_data.action = anim_rig.animation_data.action
fbx_rig.animation_data.action_slot = anim_rig.animation_data.action_slot
bpy.context.scene.frame_set(112)
error = geometry_error(reference_reach, coordinates(fbx_mesh))
assert error["max_m"] < .002, error
results["FBX_demo_roundtrip"] = {"frame_range": list(anim_rig.animation_data.action.frame_range),
                                "comparison_frame": 112, **error}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT / "Possessed_Doll_Seated.glb"))
glb_mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
glb_rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
assert {b.name for b in glb_rig.data.bones} == expected_bones
error = geometry_error(reference_rest, coordinates(glb_mesh))
assert error["max_m"] < .0001, error
results["GLB_bind_roundtrip"] = {"bones": len(glb_rig.data.bones), "vertices": len(glb_mesh.data.vertices), **error}
source = OUT.parent / "possessed_doll.glb"
results["original_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
assert results["original_sha256"] == "c2060df6759e0ff3f84106e9ad649058f9b728108b0b7f31d5afd001e8c0bc71"
results["status"] = "PASS"
(OUT / "Export_Roundtrip_Validation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print("DOLL_VALIDATION_PASS", json.dumps(results))

# Render a reviewable six-second motion preview at 15 samples per second.
bpy.ops.wm.open_mainfile(filepath=str(OUT / "Possessed_Doll_Seated_Rig.blend"))
scene = bpy.context.scene
scene.render.resolution_x = 640
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
frames = QA / "DemoFrames"
frames.mkdir(exist_ok=True)
for i, frame in enumerate(range(1, 181, 2)):
    scene.frame_set(frame)
    scene.render.filepath = str(frames / (f"frame_{i:04d}.png"))
    bpy.ops.render.render(write_still=True)
print("DOLL_DEMO_FRAMES_COMPLETE", str(frames))
