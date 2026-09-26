"""Validate source motion, foot planting, skin weights and exported FBXs/GLB."""
import hashlib
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

OUT = Path(r"F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Mobile")
QA = Path(r"F:\Carnival\Saved\HauntedDollMobile")
manifest = json.loads((OUT / "Animation_Manifest.json").read_text())
results = {"engine_import_tested": False}


def coords(mesh):
    bpy.context.view_layer.update()
    ob = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = ob.to_mesh()
    xyz = [ob.matrix_world @ v.co for v in data.vertices]
    ob.to_mesh_clear()
    return xyz


def error(reference, actual):
    tree = KDTree(len(reference))
    for i, point in enumerate(reference):
        tree.insert(point, i)
    tree.balance()
    distances = [tree.find(point)[2] for point in actual]
    return {"max_m": max(distances), "p99_m": float(np.percentile(distances, 99))}


def reset(rig):
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    rig.update_tag()
    bpy.context.view_layer.update()


bpy.ops.wm.open_mainfile(filepath=str(OUT / "Possessed_Doll_Mobile_Rig.blend"))
bpy.ops.object.mode_set(mode="OBJECT")
rig = bpy.data.objects["Doll_Mobile_Rig"]
mesh = bpy.data.objects["Possessed_Doll_Mobile"]
scene = bpy.context.scene
expected = {b.name for b in rig.data.bones if b.use_deform}
assert len(expected) == 26
assert len(rig.data.bones) == 34
assert len([b for b in rig.data.bones if not b.parent]) == 1
assert {a.name for a in bpy.data.actions} == {m["name"] for m in manifest}
assert all(len(v.groups) <= 4 for v in mesh.data.vertices)
weight_error = max(abs(sum(g.weight for g in v.groups) - 1) for v in mesh.data.vertices)
assert weight_error < .0001, weight_error
assert all(g.group < len(mesh.vertex_groups) and g.weight > 0 for v in mesh.data.vertices for g in v.groups)
assert all(mesh.vertex_groups[g.group].name in expected for v in mesh.data.vertices for g in v.groups)
assert len([im for im in bpy.data.images if im.packed_file]) == 3
assert not mesh.data.shape_keys
reset(rig)
bind = coords(mesh)
groups = {g.index: g.name for g in mesh.vertex_groups}
shoe_vertices = {s: [v.co.copy() for v in mesh.data.vertices
                     if any(groups[g.group] == "foot_" + s and g.weight > .999 for g in v.groups)] for s in ["l", "r"]}
leg_faces = [tuple(p.vertices) for p in mesh.data.polygons if p.material_index == 1]
# Analytic winding sanity check on the modeled leg shafts in bind pose.
leg_winding = []
for p in mesh.data.polygons:
    if p.material_index != 1 or abs(p.normal.z) > .85:
        continue
    cx = .112 if p.center.x > 0 else -.112
    outward = Vector((p.center.x - cx, p.center.y - .24, 0))
    leg_winding.append(p.normal.dot(outward))
assert min(leg_winding) > 0, min(leg_winding)
results["skin"] = {"vertices": len(mesh.data.vertices), "polygons": len(mesh.data.polygons),
                   "export_bones": len(expected), "bones_with_controls": len(rig.data.bones),
                   "max_influences": max(len(v.groups) for v in mesh.data.vertices),
                   "max_weight_sum_error": weight_error, "new_leg_normals_outward": True,
                   "packed_textures": 3}

references = {}
motion_results = []
for item in manifest:
    name = item["name"]
    action = bpy.data.actions[name]
    rig.animation_data.action = action
    start, end = item["frames"]
    snapshots = {}
    sample_frames = sorted(set([start, start + (end - start) // 4,
                                start + (end - start) // 2, start + 3 * (end - start) // 4, end]))
    lowest = math.inf
    worst_ik = 0.0
    planted_error = 0.0
    stance_start = {"l": None, "r": None}
    initial = None
    for frame in range(start, end + 1):
        scene.frame_set(frame)
        if frame in sample_frames:
            snapshots[frame] = coords(mesh)
        root_move = rig.pose.bones["root"].matrix.translation - rig.data.bones["root"].head_local
        transforms = {b.name: b.matrix.copy() for b in rig.pose.bones if b.name in expected}
        if frame == start:
            initial = transforms
        for side, shift in [("l", 0), ("r", .5)]:
            calf = rig.pose.bones["calf_" + side]
            control = rig.pose.bones["CTRL_foot_IK_" + side]
            worst_ik = max(worst_ik, (calf.tail - control.head).length)
            foot = rig.pose.bones["foot_" + side]
            mat = foot.matrix @ foot.bone.matrix_local.inverted()
            bottom = min((mat @ v).z for v in shoe_vertices[side])
            lowest = min(lowest, bottom)
            if name.endswith("RootMotion"):
                phase = (((frame - 1) / 30) / item["duration_seconds"] + shift) % 1
                duty = .42 if "Run" in name else .62
                in_stance = phase < duty
                if in_stance:
                    point = foot.head.copy()
                    # Restart measurement when phase wraps across the loop edge.
                    old = stance_start[side]
                    if old is None or phase < old[0]:
                        stance_start[side] = (phase, point)
                    else:
                        planted_error = max(planted_error, (point - old[1]).length)
                else:
                    stance_start[side] = None
    assert worst_ik < .0001, (name, worst_ik)
    assert lowest > -.002, (name, lowest)
    assert planted_error < .0001, (name, planted_error)
    loop_error = None
    if item["loop"]:
        loop_error = 0.0
        for bname, matrix in transforms.items():
            adjusted = matrix.copy()
            adjusted.translation -= root_move
            loop_error = max(loop_error, float(np.abs(np.array(adjusted) - np.array(initial[bname])).max()))
        assert loop_error < .0001, (name, loop_error)
    motion_results.append({"name": name, "minimum_shoe_z_m": lowest,
                           "max_leg_IK_error_m": worst_ik, "stance_foot_drift_m": planted_error,
                           "loop_transform_error": loop_error})
    references[name] = snapshots
results["motion"] = motion_results

# Round-trip into a clean scene: this verifies actual exported deformation,
# including IK and all six skirt bones, against the authored Blender motions.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.fbx(filepath=str(OUT / "Possessed_Doll_Mobile.fbx"), use_anim=False)
fbx_mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
fbx_rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
assert {b.name for b in fbx_rig.data.bones} == expected
bind_error = error(bind, coords(fbx_mesh))
assert bind_error["max_m"] < .0001, bind_error
results["FBX_bind_roundtrip"] = bind_error
textures = [{"name": im.name, "resolved": Path(bpy.path.abspath(im.filepath)).is_file()}
            for im in bpy.data.images if im.source == "FILE"]
assert len(textures) >= 2 and all(im["resolved"] for im in textures), textures
results["FBX_textures"] = textures
fbx_results = []
for item in manifest:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(OUT / "Animations" / (item["name"] + ".fbx")), use_anim=True, anim_offset=0)
    anim = next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE")
    assert {b.name for b in anim.data.bones} == expected
    assert list(anim.animation_data.action.frame_range) == item["frames"]
    fbx_rig.animation_data_create()
    fbx_rig.animation_data.action = anim.animation_data.action
    fbx_rig.animation_data.action_slot = anim.animation_data.action_slot
    samples = []
    for frame, reference in references[item["name"]].items():
        bpy.context.scene.frame_set(frame)
        err = error(reference, coords(fbx_mesh))
        assert err["max_m"] < .0005, (item["name"], frame, err)
        samples.append({"frame": frame, **err})
    fbx_results.append({"name": item["name"], "samples": samples})
    bpy.data.objects.remove(anim, do_unlink=True)
results["FBX_animation_roundtrips"] = fbx_results

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT / "Possessed_Doll_Mobile.glb"))
glb_rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
glb_mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
assert {b.name for b in glb_rig.data.bones} == expected
glb_error = error(bind, coords(glb_mesh))
assert glb_error["max_m"] < .0001, glb_error
results["GLB_bind_roundtrip"] = glb_error
results["source_sha256"] = hashlib.sha256((OUT.parent / "possessed_doll.glb").read_bytes()).hexdigest()
assert results["source_sha256"] == "c2060df6759e0ff3f84106e9ad649058f9b728108b0b7f31d5afd001e8c0bc71"
results["status"] = "PASS"
(OUT / "Export_Roundtrip_Validation.json").write_text(json.dumps(results, indent=2))
print("MOBILE_VALIDATION_PASS", json.dumps({k: v for k, v in results.items() if k not in ["FBX_animation_roundtrips", "motion"]}))
