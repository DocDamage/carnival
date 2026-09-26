"""Create a separate standing/mobile doll from the tested seated asset.

Blender 4.5.5, no add-ons. The source GLB and seated deliverables are not changed.
"""
import json
import math
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector

BASE = Path(r"F:\3D Characters\Metahuman Downloads\Possessed Doll")
OUT = BASE / "Rigged_Mobile"
QA = Path(r"F:\Carnival\Saved\HauntedDollMobile")
for p in [OUT, OUT / "Textures", OUT / "Previews", QA]:
    p.mkdir(parents=True, exist_ok=True)
SEATED_OFFSET = .49419888854026794
HIP_Y = .24
ANKLE_Z = -.80
SHOE_ANGLE = math.radians(50)

bpy.ops.wm.open_mainfile(filepath=str(BASE / "Rigged_Seated" / "Possessed_Doll_Seated_Rig.blend"))
bpy.context.preferences.filepaths.save_version = 0
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
scene = bpy.context.scene
rig = bpy.data.objects["Doll_Seated_Rig"]
rig.name = "Doll_Mobile_Rig"
rig.data.name = "Doll_Mobile_Skeleton"
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.rotation_euler = (0, 0, 0)
    pb.location = (0, 0, 0)
for side in ["L", "R"]:
    rig.pose.bones["root"]["Hand IK " + side] = 0.0
rig.update_tag()
bpy.context.view_layer.update()
mesh = bpy.data.objects["Possessed_Doll"]
mesh.name = "Doll_Body_and_Dress"
coords = np.array([v.co[:] for v in mesh.data.vertices])
coords[:, 2] -= SEATED_OFFSET
unique, inv = np.unique(np.round(coords, 6), axis=0, return_inverse=True)
edges = np.array([[inv[e.vertices[0]], inv[e.vertices[1]]] for e in mesh.data.edges])
edges = np.unique(np.sort(edges, axis=1), axis=0)


def foot_regions(cut):
    eligible = unique[:, 1] < cut
    links = edges[eligible[edges].all(axis=1)]
    parent = np.arange(len(unique))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b in links:
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a
    labels = np.array([find(i) for i in range(len(unique))])
    result = {}
    for side, sign in [("l", 1), ("r", -1)]:
        candidates = np.where(eligible & (unique[:, 0] * sign > .05))[0]
        seed = candidates[np.argmin(unique[candidates, 1])]
        selection = eligible & (labels == labels[seed])
        q = unique[selection]
        assert np.all(q[:, 0] * sign > .01), "Foot merged with dress at cut; review segmentation"
        result[side] = selection[inv]
    return result


remove_legs = foot_regions(-.18)
retain_shoes = foot_regions(-.275)
character = mesh.users_collection[0]
shoes = []
shoe_points = []
for side, sign in [("l", 1), ("r", -1)]:
    ob = mesh.copy()
    ob.data = mesh.data.copy()
    ob.name = "Doll_Shoe_" + side
    character.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not retain_shoes[side][v.index]], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    pivot = Vector((sign * .112, -.33, -.32))
    destination = Vector((sign * .112, HIP_Y, ANKLE_Z))
    rotation = Matrix.Rotation(SHOE_ANGLE, 3, "X")
    for v in ob.data.vertices:
        p = v.co - Vector((0, 0, SEATED_OFFSET))
        v.co = destination + rotation @ (p - pivot)
        shoe_points.append(v.co.copy())
    ob.vertex_groups.clear()
    ob.vertex_groups.new(name="foot_" + side).add(list(range(len(ob.data.vertices))), 1, "REPLACE")
    shoes.append(ob)

# Delete the old visible shins from the body; the new leg mesh fills the space.
remove = remove_legs["l"] | remove_legs["r"]
bm = bmesh.new()
bm.from_mesh(mesh.data)
bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if remove[v.index]], context="VERTS")
bm.to_mesh(mesh.data)
bm.free()


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def drape(p):
    x, y, z = p
    blend = float(smooth(-.145, -.20, z))
    dy = y - HIP_Y
    radius = math.sqrt((x / .38) ** 2 + (dy / (.49 if dy < 0 else .255)) ** 2)
    return Vector((x * (1 - .1 * blend), HIP_Y + dy * (1 - .5 * blend),
                   z * (1 - blend) + blend * (-.17 + .55 * (z + .17) - .34 * smooth(.28, .95, radius))))


groups = {g.index: g.name for g in mesh.vertex_groups}
for v in mesh.data.vertices:
    p = v.co - Vector((0, 0, SEATED_OFFSET))
    arm = sum(g.weight for g in v.groups if any(s in groups[g.group] for s in ["arm_", "hand_"]))
    if arm < .5 and p.z < -.145:
        v.co = drape(p)
    else:
        v.co = p
    # The remnants under the old hem should no longer follow a distant foot.
    foot_weight = sum(g.weight for g in v.groups if groups[g.group].startswith("foot_"))
    if foot_weight:
        current = next((g.weight for g in v.groups if groups[g.group] == "pelvis"), 0)
        mesh.vertex_groups["pelvis"].add([v.index], current + foot_weight, "REPLACE")
        for side in ["l", "r"]:
            mesh.vertex_groups["foot_" + side].remove([v.index])

# Position the standing floor from the retained shoe geometry, not a guessed height.
ground = -min(p.z for p in shoe_points)
offset = Vector((0, 0, ground))
for ob in [mesh, *shoes]:
    for v in ob.data.vertices:
        v.co += offset

# Reweight the hanging skirt around its new waist, with a smooth left/right
# split. The seated hem weights leave too much of the standing skirt on pelvis.
for v in mesh.data.vertices:
    p = v.co - offset
    arm = sum(g.weight for g in v.groups if any(s in groups[g.group] for s in ["arm_", "hand_"]))
    amount = float(smooth(-.175, -.37, p.z))
    if amount == 0 or arm > .1:
        continue
    original = {groups[g.group]: g.weight for g in v.groups}
    original = {n: w for n, w in original.items() if not n.startswith("dress_")}
    if not original:
        original = {"pelvis": 1.0}
    total = sum(original.values())
    weights = {n: (1 - amount) * w / total for n, w in original.items()}
    left = float(smooth(-.045, .045, p.x))
    front = float(smooth(.015, -.11, p.y - HIP_Y))
    back = float(smooth(.015, .095, p.y - HIP_Y))
    lateral = max(0.0, 1 - front - back)
    for side, fraction in [("l", left), ("r", 1 - left)]:
        for part, sector in [("front", front), ("side", lateral), ("back", back)]:
            weights["dress_" + part + "_" + side] = amount * fraction * sector
    weights = dict(sorted(weights.items(), key=lambda item: item[1], reverse=True)[:4])
    total = sum(weights.values())
    for group in mesh.vertex_groups:
        group.remove([v.index])
    for name, weight in weights.items():
        if weight > .00001:
            mesh.vertex_groups[name].add([v.index], weight / total, "REPLACE")

bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
for b in rig.data.edit_bones:
    b.head.z -= SEATED_OFFSET
    b.tail.z -= SEATED_OFFSET
    if b.name.startswith("dress_"):
        b.head = drape(b.head)
        b.tail = drape(b.tail)
    b.head += offset
    b.tail += offset
root = rig.data.edit_bones["root"]
root.head = (0, HIP_Y, 0)
root.tail = (0, HIP_Y, .12)


def add_bone(name, head, tail, parent, deform=True):
    b = rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name)
    b.head = Vector(head) + offset
    b.tail = Vector(tail) + offset
    b.parent = rig.data.edit_bones[parent]
    b.use_deform = deform
    b.use_connect = False
    b.align_roll(Vector((0, 1, 0)))
    return b


for side, sign in [("l", 1), ("r", -1)]:
    hip = (sign * .112, HIP_Y, -.28)
    knee = (sign * .112, .22, -.55)
    ankle = (sign * .112, HIP_Y, ANKLE_Z)
    toe = (sign * .112, .08, ANKLE_Z - .06)
    add_bone("thigh_" + side, hip, knee, "pelvis")
    add_bone("calf_" + side, knee, ankle, "thigh_" + side)
    add_bone("foot_" + side, ankle, toe, "calf_" + side)
    add_bone("CTRL_foot_IK_" + side, ankle, toe, "root", False)
    add_bone("CTRL_knee_" + side, (sign * .112, -.20, -.53), (sign * .112, -.20, -.47), "root", False)
    for part in ["front", "side", "back"]:
        dress = rig.data.edit_bones["dress_" + part + "_" + side]
        dress.head = Vector((sign * .112, HIP_Y, -.20)) + offset
        dress.align_roll(Vector((0, 1, 0)))
bpy.ops.object.mode_set(mode="OBJECT")

# New hidden thighs and visible porcelain shins. Their original boot meshes remain.
leg_material = bpy.data.materials.new("Doll_Porcelain_Legs")
leg_material.use_nodes = True
nodes = leg_material.node_tree.nodes
links = leg_material.node_tree.links
bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Roughness"].default_value = .62
texcoord = nodes.new("ShaderNodeTexCoord")
mapping = nodes.new("ShaderNodeVectorMath")
mapping.operation = "MULTIPLY"
mapping.inputs[1].default_value = (7, 11, 1)
links.new(texcoord.outputs["UV"], mapping.inputs[0])
voronoi = nodes.new("ShaderNodeTexVoronoi")
voronoi.voronoi_dimensions = "2D"
voronoi.feature = "DISTANCE_TO_EDGE"
voronoi.inputs["Scale"].default_value = 1
links.new(mapping.outputs[0], voronoi.inputs["Vector"])
ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = .004
ramp.color_ramp.elements[0].color = (.038, .034, .029, 1)
ramp.color_ramp.elements[1].position = .017
ramp.color_ramp.elements[1].color = (.61, .61, .55, 1)
links.new(voronoi.outputs["Distance"], ramp.inputs[0])
links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

legs = []
for side, sign in [("l", 1), ("r", -1)]:
    # Ring profiles include the covered thigh and a taper into the retained boot.
    profile = [(-.265, .073, .24), (-.31, .07, .24), (-.42, .061, .23),
               (-.51, .049, .22), (-.55, .047, .22), (-.585, .047, .223),
               (-.66, .052, .229), (-.73, .047, .235), (-.795, .042, .24)]
    count = 32
    verts, faces, uvs = [], [], []
    for j, (z, radius, cy) in enumerate(profile):
        for i in range(count + 1):
            angle = 2 * math.pi * i / count
            verts.append((sign * .112 + radius * math.cos(angle), cy + radius * math.sin(angle), z + ground))
            uvs.append((i / count, j / (len(profile) - 1)))
    for j in range(len(profile) - 1):
        for i in range(count):
            a = j * (count + 1) + i
            faces.append((a, a + 1, a + count + 2, a + count + 1))
    faces.extend([tuple(range(count, -1, -1)), tuple((len(profile) - 1) * (count + 1) + i for i in range(count + 1))])
    # Profile rings run downward: reverse winding so porcelain renders correctly
    # in engines with backface culling enabled.
    faces = [tuple(reversed(face)) for face in faces]
    data = bpy.data.meshes.new("PorcelainLeg_" + side)
    data.from_pydata(verts, [], faces)
    data.materials.append(leg_material)
    uv = data.uv_layers.new(name="UVMap")
    for face in data.polygons:
        face.use_smooth = True
        for li in face.loop_indices:
            uv.data[li].uv = uvs[data.loops[li].vertex_index]
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.000001)
    bm.to_mesh(data)
    bm.free()
    ob = bpy.data.objects.new("Doll_Leg_" + side, data)
    character.objects.link(ob)
    ob.parent = rig
    thigh_group = ob.vertex_groups.new(name="thigh_" + side)
    calf_group = ob.vertex_groups.new(name="calf_" + side)
    for v in data.vertices:
        weight = float(smooth(-.51, -.585, v.co.z - ground))
        if weight < 1:
            thigh_group.add([v.index], 1 - weight, "REPLACE")
        if weight > 0:
            calf_group.add([v.index], weight, "REPLACE")
    mod = ob.modifiers.new("Mobile doll skin", "ARMATURE")
    mod.object = rig
    legs.append(ob)

# Bake the new shin material to a portable image; no procedural shader is required
# by exported assets. This is a standard Blender material bake, not an AI texture.
image = bpy.data.images.new("Doll_Legs_BaseColor", width=1024, height=1024, alpha=False)
image.colorspace_settings.name = "sRGB"
bake_node = nodes.new("ShaderNodeTexImage")
bake_node.image = image
nodes.active = bake_node
emission = nodes.new("ShaderNodeEmission")
links.new(ramp.outputs["Color"], emission.inputs["Color"])
output_node = nodes.get("Material Output")
links.new(emission.outputs[0], output_node.inputs["Surface"])
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
bpy.ops.object.select_all(action="DESELECT")
legs[0].select_set(True)
bpy.context.view_layer.objects.active = legs[0]
bpy.ops.object.bake(type="EMIT", margin=8)
image.filepath_raw = str(OUT / "Textures" / "Doll_Legs_BaseColor.png")
image.file_format = "PNG"
image.save()
image.pack()
links.new(bsdf.outputs[0], output_node.inputs["Surface"])
links.new(bake_node.outputs["Color"], bsdf.inputs["Base Color"])
for node in [texcoord, mapping, voronoi, ramp, emission]:
    nodes.remove(node)

# Hand drivers from the seated rig are retained. Add two-bone leg IK.
leg_controls = rig.data.collections.new("Legs - IK feet and knees")
leg_fk = rig.data.collections.new("Legs - deform bones")
leg_fk.is_visible = False
square = bpy.data.objects["WGT_square"]
diamond = bpy.data.objects["WGT_diamond"]
ik_report = []
for side in ["l", "r"]:
    for prefix in ["thigh_", "calf_", "foot_", "CTRL_foot_IK_", "CTRL_knee_"]:
        pb = rig.pose.bones[prefix + side]
        pb.rotation_mode = "XYZ"
        pb.lock_scale = (True, True, True)
        pb.custom_shape = diamond if "knee" in prefix else square
        pb.use_custom_shape_bone_size = False
        pb.custom_shape_scale_xyz = (.045,) * 3
        pb.bone.color.palette = "THEME04"
        (leg_controls if prefix.startswith("CTRL_") else leg_fk).assign(pb.bone)
        if not prefix.startswith("CTRL_"):
            pb.lock_location = (True, True, True)
    calf = rig.pose.bones["calf_" + side]
    baseline = calf.head.copy()
    ik = calf.constraints.new("IK")
    ik.name = "Grounded leg IK"
    ik.target = rig
    ik.subtarget = "CTRL_foot_IK_" + side
    ik.pole_target = rig
    ik.pole_subtarget = "CTRL_knee_" + side
    ik.chain_count = 2
    ik.use_stretch = False
    calf.ik_stretch = 0
    rig.pose.bones["thigh_" + side].ik_stretch = 0
    best, err = 0, float("inf")
    for step, center, n in [(math.pi / 64, 0, 64), (.004, None, 12), (.0002, None, 20)]:
        center = best if center is None else center
        for angle in np.linspace(center - n * step, center + n * step, 2 * n + 1):
            ik.pole_angle = float(angle)
            bpy.context.view_layer.update()
            error = (calf.head - baseline).length
            if error < err:
                best, err = float(angle), error
    ik.pole_angle = best
    rot = rig.pose.bones["foot_" + side].constraints.new("COPY_ROTATION")
    rot.target = rig
    rot.subtarget = "CTRL_foot_IK_" + side
    rot.owner_space = "WORLD"
    rot.target_space = "WORLD"
    ik_report.append({"side": side, "rest_knee_error_m": err, "pole_angle": best})

# Use local copies of both original texture files and keep the Blender file packed.
for im in list(bpy.data.images):
    if im.name in ["Doll_BaseColor", "Doll_MetallicRoughness"]:
        filename = im.name + ".png"
        (OUT / "Textures" / filename).write_bytes(bytes(im.packed_file.data))
        im.filepath = str(OUT / "Textures" / filename)
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 800
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
stage = bpy.data.collections["PREVIEW | Cameras and lighting"]
stage.hide_viewport = False
scene.frame_start = 1
scene.frame_end = 60
scene.frame_set(1)
target = Vector((0, .20, (ground + .50) * .51))
scene.camera.data.ortho_scale = (ground + .50) * 1.27
scene.camera.location = (1.6, -4.5, 1.3)
scene.camera.rotation_euler = (target - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
for name, location in [("front", (0, -4.5, 1.0)), ("three_quarter", (1.6, -4.5, 1.3)), ("side", (4.5, .20, 1.0)), ("back", (0, 4.5, 1.0))]:
    scene.camera.location = location
    scene.camera.rotation_euler = (target - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(OUT / "Previews" / ("Standing_" + name + ".png"))
    bpy.ops.render.render(write_still=True)
scene.camera.location = (1.6, -4.5, 1.3)
scene.camera.rotation_euler = (target - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
stage.hide_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "Possessed_Doll_Mobile_Rig.blend"))
report = {"ground_translation_m": ground, "standing_height_m": ground + .50,
          "deform_bones": [b.name for b in rig.data.bones if b.use_deform],
          "bones": len(rig.data.bones), "leg_ik": ik_report,
          "meshes": {o.name: len(o.data.vertices) for o in [mesh, *shoes, *legs]},
          "reconstruction": "Original upper body and shoes, re-draped original skirt, newly modeled porcelain thighs and shins"}
(OUT / "Mobile_Build_Report.json").write_text(json.dumps(report, indent=2))
print("MOBILE_BASE_BUILT", json.dumps(report))
