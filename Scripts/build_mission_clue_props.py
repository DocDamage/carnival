"""Build readable glove, note, and brass-key props for the mansion clues."""

import json
import math
from pathlib import Path

import bpy


ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/MissionAuthoring/Source/FBX"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, metallic, roughness):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1.0)
    value.use_nodes = True
    shader = value.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return value


def bevel_object(obj, width, segments=3):
    modifier = obj.modifiers.new("Soft manufactured edges", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    normal = obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=normal.name)


def add_cube(parts, name, size, position, mat, bevel=0.0, rotation=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position, rotation=(0.0, 0.0, rotation))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        bevel_object(obj, bevel)
    parts.append(obj)
    return obj


def add_ellipsoid(parts, name, position, size, mat, rotation=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    obj.rotation_euler.z = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    parts.append(obj)
    return obj


def add_cylinder(parts, name, radius, length, position, mat, rotation=(0.0, 0.0, 0.0), vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=length, location=position, rotation=rotation
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bevel_object(obj, min(radius * 0.35, length * 0.12), segments=2)
    parts.append(obj)
    return obj


def add_torus(parts, name, major, minor, position, mat):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=24, minor_segments=8, major_radius=major, minor_radius=minor, location=position
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    parts.append(obj)
    return obj


def add_note_ink_stroke(parts, name, length, y, phase, mat):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.055
    curve.bevel_resolution = 1
    spline = curve.splines.new("POLY")
    point_count = 24
    spline.points.add(point_count - 1)
    start_x = -7.25
    for index, point in enumerate(spline.points):
        alpha = index / (point_count - 1)
        x = start_x + length * alpha
        wave = 0.12 * math.sin(alpha * math.pi * 2.8 + phase)
        hand = 0.025 * math.sin(alpha * math.pi * 6.4 + phase * 1.7)
        point.co = (x, y + wave + hand, 0.225, 1.0)
    curve.materials.append(mat)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.select_set(False)
    parts.append(obj)
    return obj


def export_joined(parts, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    joined = bpy.context.object
    joined.name = name
    joined.data.name = name
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    for face in joined.data.polygons:
        face.use_smooth = True

    blend_path = OUT / f"{name}.blend"
    fbx_path = OUT / f"{name}.fbx"
    bpy.ops.object.select_all(action="DESELECT")
    joined.select_set(True)
    bpy.context.view_layer.objects.active = joined
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path), use_selection=True, object_types={"MESH"}, bake_anim=False,
        axis_forward="-Y", axis_up="Z", apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", path_mode="RELATIVE", mesh_smooth_type="SMOOTH_GROUP",
        use_mesh_modifiers=True,
    )
    return {
        "asset": name,
        "fbx": str(fbx_path),
        "blend": str(blend_path),
        "dimensions_cm": [round(value, 2) for value in joined.dimensions],
        "vertices": len(joined.data.vertices),
        "faces": len(joined.data.polygons),
        "materials": [slot.name for slot in joined.data.materials],
    }


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 0.01

glove = material("WetWorkGlove", (0.32, 0.22, 0.075), 0.02, 0.27)
cuff = material("GloveCuffCanvas", (0.085, 0.12, 0.075), 0.0, 0.58)
stitch = material("GloveSafetyStitch", (0.78, 0.39, 0.08), 0.05, 0.44)
glove_parts = []
add_cube(glove_parts, "Glove palm", (12.8, 8.0, 2.6), (-2.2, 0.0, 1.65), glove, 1.15)
add_cube(glove_parts, "Wrist cuff", (5.8, 8.5, 3.0), (-10.0, 0.0, 1.65), cuff, 1.0)
add_cube(glove_parts, "Cuff seam", (0.65, 8.65, 3.12), (-7.0, 0.0, 1.65), stitch, 0.25)
for index, (y, length) in enumerate(((-2.8, 7.1), (-0.95, 8.1), (0.95, 8.4), (2.8, 7.3))):
    add_ellipsoid(
        glove_parts, f"Glove finger {index + 1}", (3.4 + length * 0.5, y, 1.48),
        (length, 1.75, 2.25), glove, math.radians((y / 2.8) * 8.0),
    )
add_ellipsoid(glove_parts, "Glove thumb base", (0.2, -4.2, 1.45), (4.0, 2.45, 2.1), glove, math.radians(-28.0))
add_ellipsoid(glove_parts, "Glove thumb tip", (2.2, -5.8, 1.3), (3.2, 2.0, 1.9), glove, math.radians(-36.0))

brass = material("AgedServiceBrass", (0.52, 0.29, 0.075), 0.82, 0.26)
dark_brass = material("KeyBowInset", (0.09, 0.055, 0.02), 0.68, 0.31)
key_parts = []
add_torus(key_parts, "Round service key bow", 2.15, 0.62, (-4.2, 0.0, 0.72), brass)
add_torus(key_parts, "Bow inset ring", 1.18, 0.16, (-4.2, 0.0, 0.74), dark_brass)
add_cylinder(key_parts, "Key shaft", 0.66, 7.7, (0.0, 0.0, 0.7), brass, rotation=(0.0, math.pi / 2.0, 0.0))
add_cube(key_parts, "First key tooth", (1.25, 1.0, 1.05), (2.35, -0.83, 0.68), brass, 0.18)
add_cube(key_parts, "Second key tooth", (1.2, 1.0, 1.05), (3.65, 0.83, 0.68), brass, 0.18)
add_cylinder(key_parts, "End cap", 0.9, 0.7, (4.2, 0.0, 0.7), brass, rotation=(0.0, math.pi / 2.0, 0.0))

paper = material("FoyerNotePaper", (0.76, 0.68, 0.50), 0.0, 0.92)
ink = material("FoyerNoteInk", (0.075, 0.047, 0.030), 0.0, 0.88)
crease = material("FoyerNoteCrease", (0.61, 0.52, 0.37), 0.0, 0.95)
note_parts = []
add_cube(note_parts, "Folded paper note", (17.5, 12.5, 0.20), (0.0, 0.0, 0.10), paper, 0.16)
# Soft creases and a folded corner give the sheet a readable physical surface.
for index, (length, x, y, rotation) in enumerate((
    (8.0, -3.0, -5.2, math.radians(5.0)),
    (10.0, 2.4, 5.6, math.radians(-8.0)),
)):
    add_cube(note_parts, f"Paper crease {index + 1}", (length, 0.055, 0.018), (x, y, 0.213), crease, 0.02, rotation)
for index, (length, y) in enumerate((
    (7.5, 4.55),
    (11.6, 2.95),
    (10.8, 1.75),
    (11.2, 0.55),
    (8.2, -0.65),
    (10.6, -1.85),
    (8.8, -3.05),
    (6.2, -4.25),
)):
    add_note_ink_stroke(note_parts, f"Handwritten line {index + 1}", length, y, index * 0.93, ink)

results = [
    export_joined(glove_parts, "SM_WetWorkGlove"),
    export_joined(note_parts, "SM_EliFoyerNote"),
    export_joined(key_parts, "SM_BrassServiceKey"),
]
report_path = ROOT / "Saved/MissionAuthoring/Mission_Clue_Props_Source.json"
report_path.write_text(json.dumps({"props": results}, indent=2), encoding="utf-8")
print("MISSION_CLUE_PROPS_CREATED", json.dumps({"props": results}), flush=True)
