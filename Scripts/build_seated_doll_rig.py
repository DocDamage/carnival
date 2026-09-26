"""Build the seated possessed doll rig with Blender 4.5 (no add-ons required).

Run with blender --background --factory-startup --python THIS_FILE.
The original GLB is read only. Outputs live in its Rigged_Seated subfolder.
"""

import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler, Vector

SOURCE = Path(r"F:\3D Characters\Metahuman Downloads\Possessed Doll\possessed_doll.glb")
OUT = SOURCE.parent / "Rigged_Seated"
QA = Path(r"F:\Carnival\Saved\HauntedDollRig")
OUT.mkdir(exist_ok=True)
QA.mkdir(parents=True, exist_ok=True)
(OUT / "Textures").mkdir(exist_ok=True)
(OUT / "Previews").mkdir(exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
mesh.name = "Possessed_Doll"
mesh.data.name = "Possessed_Doll_Surface"
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
world = mesh.matrix_world.copy()
mesh.parent = None
mesh.matrix_world = world
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for ob in list(bpy.data.objects):
    if ob.type == "EMPTY":
        bpy.data.objects.remove(ob, do_unlink=True)

# Work in the GLB's original metric coordinates, then place the seated base on Z=0.
source_coords = np.array([v.co[:] for v in mesh.data.vertices], dtype=np.float64)
floor_z = float(source_coords[:, 2].min())
offset = Vector((0, 0, -floor_z))
for v in mesh.data.vertices:
    v.co += offset
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 181

character = bpy.data.collections.new("DOLL | Rig and mesh")
scene.collection.children.link(character)
for c in list(mesh.users_collection):
    c.objects.unlink(mesh)
character.objects.link(mesh)
shapes = bpy.data.collections.new("DOLL | Control shapes (hidden)")
scene.collection.children.link(shapes)
shapes.hide_render = True
shapes.hide_viewport = True
stage = bpy.data.collections.new("PREVIEW | Cameras and lighting")
scene.collection.children.link(stage)

arm_data = bpy.data.armatures.new("Doll_Seated_Skeleton")
rig = bpy.data.objects.new("Doll_Seated_Rig", arm_data)
character.objects.link(rig)
rig.show_in_front = True
arm_data.display_type = "BBONE"
arm_data.show_names = False
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")

# Epic-style names describe deform bones; this is the doll's OWN seated skeleton.
definitions = {}


def bone(name, head, tail, parent=None, deform=True):
    b = arm_data.edit_bones.new(name)
    b.head = Vector(head) + offset
    b.tail = Vector(tail) + offset
    if parent:
        b.parent = arm_data.edit_bones[parent]
    b.use_deform = deform
    b.align_roll(Vector((0, 1, 0)))
    definitions[name] = dict(head=list(head), tail=list(tail), parent=parent, deform=deform)
    return b


bone("root", (0, .20, floor_z), (0, .20, floor_z + .10))
bone("pelvis", (0, .25, -.28), (0, .25, -.18), "root")
bone("spine_01", (0, .245, -.18), (0, .235, -.065), "pelvis")
bone("spine_02", (0, .235, -.065), (0, .23, .065), "spine_01")
bone("neck_01", (0, .23, .065), (0, .23, .135), "spine_02")
bone("head", (0, .23, .135), (0, .23, .405), "neck_01")

for side, sign in [("l", 1), ("r", -1)]:
    def p(x, y, z):
        return (x * sign, y, z)
    shoulder = p(.176, .26, .025)
    elbow = p(.273, .255, -.112)
    wrist = p(.375, .137, -.232)
    hand_end = p(.412, .122, -.298)
    bone("clavicle_" + side, p(.035, .23, .046), shoulder, "spine_02")
    bone("upperarm_" + side, shoulder, elbow, "clavicle_" + side)
    bone("lowerarm_" + side, elbow, wrist, "upperarm_" + side)
    bone("hand_" + side, wrist, hand_end, "lowerarm_" + side)
    bone("foot_" + side, p(.145, -.307, -.318), p(.145, -.458, -.247), "pelvis")
    bone("dress_front_" + side, p(.11, -.075, -.225), p(.25, -.27, -.38), "pelvis")
    bone("dress_side_" + side, p(.17, .22, -.215), p(.385, .235, -.41), "pelvis")
    bone("dress_back_" + side, p(.115, .32, -.23), p(.265, .45, -.42), "pelvis")
    bone("CTRL_hand_IK_" + side, wrist, hand_end, "root", False)
    a, b, c = map(Vector, (shoulder, elbow, wrist))
    proj = a + (c - a) * ((b - a).dot(c - a) / (c - a).length_squared)
    pole = b + (b - proj).normalized() * .26
    bone("CTRL_elbow_" + side, pole, pole + Vector((0, 0, .045)), "root", False)

bpy.ops.object.mode_set(mode="OBJECT")
deform_names = [n for n, b in definitions.items() if b["deform"]]
index = {n: i for i, n in enumerate(deform_names)}

# Weld only for the weighting calculation, preserving the source geometry and UVs.
# Seams at identical positions MUST receive identical weights.
coords, inverse = np.unique(np.round(source_coords, 6), axis=0, return_inverse=True)
edges = np.array([[inverse[e.vertices[0]], inverse[e.vertices[1]]] for e in mesh.data.edges])
edges = np.unique(np.sort(edges, axis=1), axis=0)
edges = edges[edges[:, 0] != edges[:, 1]]
parents = np.arange(len(coords))


def find(a):
    while parents[a] != a:
        parents[a] = parents[parents[a]]
        a = parents[a]
    return a


for a, b in edges:
    a, b = find(a), find(b)
    if a != b:
        parents[b] = a
components = np.array([find(i) for i in range(len(coords))])
labels, counts = np.unique(components, return_counts=True)
main_component = labels[np.argmax(counts)]
arm_components = {}
for lab, count in zip(labels, counts):
    q = coords[components == lab]
    if 100 < count < 2000 and q[:, 2].max() < 0 and q[:, 2].min() > -.35:
        arm_components["l" if q[:, 0].mean() > 0 else "r"] = lab
assert set(arm_components) == {"l", "r"}, "Source arm geometry changed; revise weights."


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


x, y, z = coords.T
ax = np.abs(x)
weights = np.zeros((len(coords), len(deform_names)), dtype=np.float64)
weights[:, index["pelvis"]] = 1


def mix_to(name, amount):
    global weights
    amount = np.clip(amount, 0, 1)
    weights *= (1 - amount[:, None])
    weights[:, index[name]] += amount


mix_to("spine_01", smooth(-.21, -.12, z))
mix_to("spine_02", smooth(-.11, .005, z))
mix_to("neck_01", smooth(.035, .11, z) * (1 - smooth(.075, .13, ax)))

# Keep the porcelain face rigid. Trailing hair follows the head but has a gradual
# join at the shoulders where the original generated mesh joins hair and blouse.
back_hair = smooth(.29, .355, y) * (1 - smooth(.19, .25, ax))
side_hair = smooth(.23, .30, y) * smooth(.145, .20, ax) * (1 - smooth(.215, .25, ax))
hair = np.maximum(back_hair, side_hair)
cutoff = .117 - .19 * hair
head_weight = smooth(cutoff - .035, cutoff + .025, z)
mix_to("head", head_weight)

for side, sign in [("l", 1), ("r", -1)]:
    side_mask = (x * sign > 0).astype(float)
    shoulder_weight = (smooth(.125, .205, ax) * smooth(-.16, -.095, z)
                       * (1 - smooth(.055, .13, z)) * (1 - head_weight) * side_mask)
    mix_to("clavicle_" + side, shoulder_weight * .24)
    mix_to("upperarm_" + side, shoulder_weight)
    # The sleeve's lower cuff and the separate forearm share the same elbow.
    cuff = smooth(-.065, -.12, z) * shoulder_weight
    mix_to("lowerarm_" + side, cuff * .6)
    forearm = components == arm_components[side]
    weights[forearm] = 0
    wrist = np.array(definitions["hand_" + side]["head"])
    direction = np.array(definitions["hand_" + side]["tail"]) - wrist
    direction /= np.linalg.norm(direction)
    hand_weight = smooth(-.018, .025, (coords - wrist) @ direction)
    weights[forearm, index["lowerarm_" + side]] = 1 - hand_weight[forearm]
    weights[forearm, index["hand_" + side]] = hand_weight[forearm]

    # Small shoe motions only; no standing/walking leg chain is manufactured.
    shoe = smooth(-.267, -.338, y) * (1 - smooth(.21, .245, ax)) * side_mask
    mix_to("foot_" + side, shoe)
    hem = smooth(-.215, -.40, z) * side_mask * (1 - shoe)
    hem[forearm] = 0
    centers = [np.array(definitions["dress_" + part + "_" + side]["tail"])
               for part in ["front", "side", "back"]]
    dist = np.array([np.sum((coords - q) ** 2, axis=1) for q in centers]).T
    sector = np.exp(-dist / .018)
    sector /= np.maximum(sector.sum(axis=1, keepdims=True), 1e-12)
    weights *= 1 - (hem * .92)[:, None]
    for j, part in enumerate(["front", "side", "back"]):
        weights[:, index["dress_" + part + "_" + side]] += hem * .92 * sector[:, j]

# Small isolated surface flecks on the head stay attached to the rigid head.
small = ~np.isin(components, [main_component, *arm_components.values()])
weights[small] = 0
weights[small, index["head"]] = 1

# Surface smoothing avoids hard boundaries through the continuous hair/dress mesh.
# Rigid anchors remain untouched. No averaging across the detached arm components.
src = np.concatenate((edges[:, 0], edges[:, 1]))
dst = np.concatenate((edges[:, 1], edges[:, 0]))
degree = np.bincount(dst, minlength=len(coords))
anchor = (z > .165) | (y < -.345) | small
anchor |= np.isin(components, list(arm_components.values())) & (z < -.267)
for _ in range(14):
    sums = np.zeros_like(weights)
    np.add.at(sums, dst, weights[src])
    average = sums / np.maximum(degree[:, None], 1)
    changed = .58 * weights + .42 * average
    changed[anchor] = weights[anchor]
    weights = changed

# Four influences per vertex keeps the exported skin inexpensive and predictable.
keep = np.argsort(weights, axis=1)[:, -4:]
trimmed = np.zeros_like(weights)
np.put_along_axis(trimmed, keep, np.take_along_axis(weights, keep, axis=1), axis=1)
trimmed[trimmed < .0001] = 0
weights = trimmed / trimmed.sum(axis=1, keepdims=True)
assert np.isfinite(weights).all()
assert np.allclose(weights.sum(axis=1), 1)
for name, j in index.items():
    group = mesh.vertex_groups.new(name=name)
    for vi in np.flatnonzero(weights[inverse, j] > 0):
        group.add([int(vi)], float(weights[inverse[vi], j]), "REPLACE")
mod = mesh.modifiers.new("Seated doll skin", "ARMATURE")
mod.object = rig
# Linear blend matches standard FBX/game-engine skinning for honest previews.
mod.use_deform_preserve_volume = False
mesh.parent = rig


def make_shape(name, kind):
    if kind == "circle":
        points = [(math.cos(a), 0, math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40, endpoint=False)]
    elif kind == "square":
        points = [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)]
    else:
        points = [(0, 0, 1), (1, 0, 0), (0, 0, -1), (-1, 0, 0)]
    data = bpy.data.meshes.new(name)
    data.from_pydata(points, [(i, (i + 1) % len(points)) for i in range(len(points))], [])
    ob = bpy.data.objects.new(name, data)
    shapes.objects.link(ob)
    ob.hide_render = True
    return ob


circle = make_shape("WGT_ring", "circle")
square = make_shape("WGT_square", "square")
diamond = make_shape("WGT_diamond", "diamond")
collections = {name: arm_data.collections.new(name) for name in
               ["Body and head", "Arms - FK", "Arms - optional IK", "Feet", "Dress"]}
for pb in rig.pose.bones:
    pb.rotation_mode = "XYZ"
    pb.lock_scale = (True, True, True)
    pb.lock_location = (pb.name not in ["root", "pelvis"] and not pb.name.startswith("CTRL_"),) * 3
    pb.custom_shape = circle
    pb.use_custom_shape_bone_size = False
    radius = .043
    group = "Body and head"
    if any(k in pb.name for k in ["clavicle", "upperarm", "lowerarm", "hand_"]):
        group = "Arms - FK"
        radius = .035
    if pb.name.startswith("CTRL_"):
        group = "Arms - optional IK"
        pb.custom_shape = square if "hand" in pb.name else diamond
        radius = .045 if "hand" in pb.name else .025
    elif pb.name.startswith("foot"):
        group = "Feet"
    elif pb.name.startswith("dress"):
        group = "Dress"
        pb.custom_shape = diamond
        radius = .025
    if pb.name == "root":
        radius = .43
    elif pb.name == "pelvis":
        radius = .19
    elif pb.name.startswith("spine"):
        radius = .13
    elif pb.name == "head":
        radius = .22
        pb.custom_shape_translation = (0, .13, 0)
    elif pb.name == "neck_01":
        radius = .065
    pb.custom_shape_scale_xyz = (radius,) * 3
    collections[group].assign(pb.bone)
    pb.bone.color.palette = "THEME03" if group == "Body and head" else (
        "THEME04" if group == "Arms - optional IK" else "THEME02" if pb.name.endswith("_l") else "THEME01")
collections["Arms - optional IK"].is_visible = False
collections["Dress"].is_visible = False
rig.pose.bones["root"]["Rig notes"] = "Seated FK rig. Optional hand IK: enable its bone collection, then set left/right hand IK to 1."

# Optional hand IK, default OFF. Match both the target position and rest orientation.
ik_constraints = []
for side in ["l", "r"]:
    key = "Hand IK " + side.upper()
    master = rig.pose.bones["root"]
    master[key] = 0.0
    master.id_properties_ui(key).update(min=0.0, max=1.0, description="0 = rotate FK arm bones; 1 = position hand IK and elbow pole controls")
    ik = rig.pose.bones["lowerarm_" + side].constraints.new("IK")
    ik.name = "Optional two-bone hand IK"
    ik.target = rig
    ik.subtarget = "CTRL_hand_IK_" + side
    ik.pole_target = rig
    ik.pole_subtarget = "CTRL_elbow_" + side
    ik.chain_count = 2
    ik.use_stretch = False
    ik.influence = 0
    rig.pose.bones["upperarm_" + side].ik_stretch = 0
    rig.pose.bones["lowerarm_" + side].ik_stretch = 0
    # Find a pole angle that exactly preserves the artist's seated rest pose.
    before = rig.pose.bones["lowerarm_" + side].head.copy()
    ik.influence = 1
    best, err = 0.0, float("inf")
    for angle in np.linspace(-math.pi, math.pi, 129):
        ik.pole_angle = float(angle)
        bpy.context.view_layer.update()
        e = (rig.pose.bones["lowerarm_" + side].head - before).length
        if e < err:
            best, err = float(angle), e
    for step in [.005, .0005, .00005]:
        for angle in np.linspace(best - step * 10, best + step * 10, 21):
            ik.pole_angle = float(angle)
            bpy.context.view_layer.update()
            e = (rig.pose.bones["lowerarm_" + side].head - before).length
            if e < err:
                best, err = float(angle), e
    ik.pole_angle = best
    ik.influence = 0
    copy = rig.pose.bones["hand_" + side].constraints.new("COPY_ROTATION")
    copy.name = "Hand follows optional IK control"
    copy.target = rig
    copy.subtarget = "CTRL_hand_IK_" + side
    copy.target_space = "WORLD"
    copy.owner_space = "WORLD"
    copy.influence = 0
    for con in [ik, copy]:
        fc = con.driver_add("influence")
        var = fc.driver.variables.new()
        var.name = "blend"
        var.type = "SINGLE_PROP"
        var.targets[0].id = rig
        var.targets[0].data_path = 'pose.bones["root"]["' + key + '"]'
        fc.driver.expression = "blend"
    ik_constraints.append({"side": side, "pole_angle": best, "rest_elbow_error_m": err})
    bpy.context.view_layer.update()

# Save textures as portable external PNGs and also pack them into the .blend.
texture_files = []
for i, im in enumerate(list(bpy.data.images)):
    if not im.packed_file:
        continue
    filename = "Doll_BaseColor.png" if i == 0 else "Doll_MetallicRoughness.png"
    # Imported GLB images are already packed with empty source paths. Image.save()
    # can update that packed payload without producing an external file. Extract
    # the original PNG bytes and relink a fresh file-backed image instead.
    path = OUT / "Textures" / filename
    assert im.packed_file, "Expected an embedded PNG in the source GLB"
    path.write_bytes(bytes(im.packed_file.data))
    colorspace = im.colorspace_settings.name
    replacement = bpy.data.images.load(str(path), check_existing=False)
    replacement.name = Path(filename).stem
    replacement.colorspace_settings.name = colorspace
    for material in bpy.data.materials:
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image == im:
                    node.image = replacement
    bpy.data.images.remove(im)
    replacement.pack()
    texture_files.append(filename)
assert len(texture_files) == 2, "Both source textures must be externalized"

scene.world = bpy.data.worlds.new("Doll preview world")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.045, .055, .075, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .45
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 800
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
target = Vector((0, .03, .52))


def light(name, loc, energy, color, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    ob = bpy.data.objects.new(name, data)
    stage.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (target - ob.location).to_track_quat("-Z", "Y").to_euler()


light("Key warm", (-1.4, -2.2, 2.6), 520, (1, .86, .73), 2)
light("Fill cool", (1.7, -1.2, 1.3), 350, (.66, .8, 1), 2)
light("Rim", (0, 1.9, 2.0), 650, (.77, .87, 1), 1.7)
camera_data = bpy.data.cameras.new("Doll preview camera")
camera = bpy.data.objects.new("Doll preview camera", camera_data)
stage.objects.link(camera)
scene.camera = camera
camera_data.type = "ORTHO"
camera_data.ortho_scale = 1.35
camera.location = (1.25, -3.5, 1.0)
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def reset_pose():
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    for side in ["L", "R"]:
        rig.pose.bones["root"]["Hand IK " + side] = 0.0
    rig.update_tag()
    bpy.context.view_layer.update()


def rotate_world(name, xyz_degrees):
    pb = rig.pose.bones[name]
    rest = pb.bone.matrix_local.to_3x3()
    rotation = Euler([math.radians(v) for v in xyz_degrees], "XYZ").to_matrix()
    pb.rotation_euler = (rest.inverted() @ rotation @ rest).to_euler("XYZ")


poses = {
    "01_rest": {},
    "02_head_turn": {"head": (0, 0, -25), "neck_01": (0, 0, -4)},
    "03_head_tilt": {"head": (5, 20, 0)},
    "04_reach": {"upperarm_l": (-38, -8, 0), "lowerarm_l": (-25, 0, -10), "hand_l": (0, -10, 0)},
    "05_both_arms": {"upperarm_l": (-32, -12, 0), "upperarm_r": (-32, 12, 0),
                     "lowerarm_l": (-22, 0, -6), "lowerarm_r": (-22, 0, 6)},
    "06_rock_and_feet": {"spine_01": (6, 0, 0), "spine_02": (3, -4, 0),
                         "foot_l": (8, 0, 0), "foot_r": (-6, 0, 0)},
}
mesh_edges = np.array([e.vertices[:] for e in mesh.data.edges])
rest_coords = source_coords + np.array(offset)
rest_lengths = np.linalg.norm(rest_coords[mesh_edges[:, 0]] - rest_coords[mesh_edges[:, 1]], axis=1)
deformation_stats = []
for name, rotations in poses.items():
    reset_pose()
    for bname, angles in rotations.items():
        rotate_world(bname, angles)
    bpy.context.view_layer.update()
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    v = np.array([p.co[:] for p in evaluated.data.vertices])
    lengths = np.linalg.norm(v[mesh_edges[:, 0]] - v[mesh_edges[:, 1]], axis=1)
    ratios = lengths / np.maximum(rest_lengths, 1e-9)
    deformation_stats.append({"pose": name, "finite": bool(np.isfinite(v).all()),
                              "edge_ratio_p99": float(np.percentile(ratios, 99)),
                              "edge_ratio_max": float(ratios.max())})
    scene.render.filepath = str(OUT / "Previews" / (name + ".png"))
    bpy.ops.render.render(write_still=True)

reset_pose()
if rig.animation_data:
    rig.animation_data.action = None
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
fbx_base = dict(use_selection=True, object_types={"ARMATURE", "MESH"},
                add_leaf_bones=False, use_armature_deform_only=True,
                axis_forward="-Y", axis_up="Z", apply_unit_scale=True,
                apply_scale_options="FBX_SCALE_UNITS", path_mode="RELATIVE")
bpy.ops.export_scene.fbx(filepath=str(OUT / "Possessed_Doll_Seated.fbx"), bake_anim=False, **fbx_base)
bpy.ops.export_scene.gltf(filepath=str(OUT / "Possessed_Doll_Seated.glb"), export_format="GLB",
                          use_selection=True, export_animations=False, export_skins=True,
                          export_def_bones=True)

# Original, small demonstration of the rig, not a retargeted commercial animation.
action = bpy.data.actions.new("Doll_Seated_Rig_Demo")
action.use_fake_user = True
rig.animation_data_create()
rig.animation_data.action = action
keys = [
    (1, {}), (31, {"head": (0, 0, -18)}),
    (51, {"head": (2, 13, -18)}), (61, {"head": (-3, -8, 10)}),
    (82, {}), (112, poses["04_reach"]), (132, poses["05_both_arms"]),
    (151, {"head": (4, 8, 0), "spine_01": (3, 0, 0)}), (181, {}),
]
for frame, rotations in keys:
    reset_pose()
    for name, angles in rotations.items():
        rotate_world(name, angles)
    for name in deform_names:
        pb = rig.pose.bones[name]
        pb.keyframe_insert(data_path="rotation_euler", frame=frame, group=name)
        pb.keyframe_insert(data_path="location", frame=frame, group=name)
scene.frame_set(1)
mesh.select_set(False)
bpy.ops.export_scene.fbx(filepath=str(OUT / "Doll_Seated_Rig_Demo.fbx"), bake_anim=True,
                          bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                          bake_anim_simplify_factor=0, **fbx_base)
mesh.select_set(True)

readme = bpy.data.texts.new("START HERE - Seated Doll Rig")
readme.write("SEATED POSSESSED DOLL\n\n"
"The supplied GLB is preserved. This is a separate, seated-only rig.\n"
"Scale is preserved: approximately 0.994 metres seated height. Root sits on Z=0.\n\n"
"POSE: Select Doll_Seated_Rig; enter Pose Mode. Rotate the coloured controls.\n"
"Body and head: pelvis, spine_01, spine_02, neck_01, head.\n"
"Arms: clavicle, upperarm, lowerarm, hand; .l is the doll's left (+X).\n"
"Feet: subtle shoe movement only. Dress helper bones are hidden by default.\n\n"
"OPTIONAL HAND IK: Show the Arms - optional IK bone collection. Select root,\n"
"set Hand IK L/R to 1 in Custom Properties. Move CTRL_hand_IK_l/r; adjust\n"
"CTRL_elbow_l/r for elbow direction. FK and IK are not automatically snapped\n"
"when switching an already posed arm. Default is FK (0).\n\n"
"DEMO: The six-second Doll_Seated_Rig_Demo action is assigned. Frame 1 is rest.\n"
"Clear the action before manual posing, or enable auto-key when animating.\n\n"
"EXPORT: Possessed_Doll_Seated.fbx is the mesh and deform skeleton in bind pose.\n"
"Doll_Seated_Rig_Demo.fbx is animation-only on the same skeleton.\n"
"The GLB keeps materials and skin. Textures are packed here and saved externally.\n\n"
"LIMITS: No face, eye, jaw, individual finger, standing, or walking rig.\n"
"The face/hair and mittens are sculpted surfaces. The original hair is partly\n"
"joined to the shoulders, so modest head movements work best. This is not the\n"
"Epic/MetaHuman skeleton; use a separate Unreal skeleton on first import.\n")

# Start with the rig selected in a useful front three-quarter pose view.
scene.frame_set(1)
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
stage.hide_viewport = True
for b in arm_data.bones:
    b.select = False
arm_data.bones.active = arm_data.bones["head"]
arm_data.bones["head"].select = True
for area in bpy.context.screen.areas:
    if area.type == "VIEW_3D":
        area.spaces.active.shading.type = "MATERIAL"
        area.spaces.active.overlay.show_floor = False
        area.spaces.active.overlay.show_axis_x = False
        area.spaces.active.overlay.show_axis_y = False
        area.spaces.active.region_3d.view_distance = 1.65
        area.spaces.active.region_3d.view_location = target
        area.spaces.active.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
        area.spaces.active.region_3d.view_perspective = "ORTHO"
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "Possessed_Doll_Seated_Rig.blend"))

report = {
    "source": str(SOURCE), "blend": str(OUT / "Possessed_Doll_Seated_Rig.blend"),
    "scope": "seated-only FK puppet rig with optional two-bone arm IK",
    "height_m": float(source_coords[:, 2].max() - floor_z),
    "source_floor_translation_m": float(-floor_z),
    "vertices": len(mesh.data.vertices), "bones": len(arm_data.bones),
    "deform_bones": deform_names, "bone_definitions_source_coordinates": definitions,
    "unweighted_vertices": int(np.sum(weights.sum(axis=1) == 0)),
    "max_influences": int((weights > 0).sum(axis=1).max()),
    "weight_sum_error": float(np.max(np.abs(weights.sum(axis=1) - 1))),
    "pose_checks": deformation_stats, "optional_ik": ik_constraints,
    "textures": texture_files,
}
(OUT / "Rig_Validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("DOLL_RIG_COMPLETE", json.dumps({k: report[k] for k in
      ["vertices", "bones", "unweighted_vertices", "max_influences", "pose_checks", "optional_ik"]}))
