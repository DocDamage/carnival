"""Create a compact, closed brass-and-rosewood music-box prop for the mansion story."""

import json
from pathlib import Path

import bpy


ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/MansionConnection/Source/FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX_PATH = OUT / "SM_BrassMusicBox.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.01


def make_material(name, color, metallic, roughness):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (*color, 1.0)
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    return material


rosewood = make_material("Rosewood", (0.11, 0.035, 0.018), 0.12, 0.3)
brass = make_material("AgedBrass", (0.62, 0.34, 0.075), 0.78, 0.24)
dark_inlay = make_material("DarkInlay", (0.035, 0.02, 0.012), 0.22, 0.27)

parts = []


def add_cube(name, dimensions, location, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel > 0.0:
        modifier = obj.modifiers.new("Soft hand-finished edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Weighted normals")
    parts.append(obj)
    return obj


def add_cylinder(name, radius, depth, location, material, rotation=(0.0, 0.0, 0.0), vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Rounded ends", "BEVEL")
    bevel.width = min(radius * 0.25, depth * 0.18)
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Weighted normals")
    parts.append(obj)
    return obj


def add_torus(name, major_radius, minor_radius, location, material):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=32,
        minor_segments=8,
        location=location,
        major_radius=major_radius,
        minor_radius=minor_radius,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    parts.append(obj)
    return obj


# Rosewood body, thin brass band, and a fitted lid.
add_cube("Box body", (40.0, 29.0, 14.0), (0.0, 0.0, 0.0), rosewood, 1.6)
add_cube("Lower brass band", (40.5, 29.5, 2.0), (0.0, 0.0, -4.3), brass, 0.55)
add_cube("Fitted lid", (40.0, 29.0, 7.0), (0.0, 0.0, 10.2), rosewood, 1.5)
add_cube("Lid brass inlay", (34.0, 0.55, 0.45), (0.0, -10.4, 13.65), brass, 0.18)
add_cube("Lid brass inlay", (34.0, 0.55, 0.45), (0.0, 10.4, 13.65), brass, 0.18)
add_cube("Lid brass inlay", (0.55, 20.0, 0.45), (-16.7, 0.0, 13.65), brass, 0.18)
add_cube("Lid brass inlay", (0.55, 20.0, 0.45), (16.7, 0.0, 13.65), brass, 0.18)
add_cube("Lid center", (20.0, 11.5, 0.7), (0.0, 0.0, 13.72), dark_inlay, 1.8)

# The center medallion and tiny corner pins give it a recognizable wind-up-box silhouette.
add_cylinder("Medallion backing", 4.1, 0.65, (0.0, 0.0, 14.25), brass)
add_cylinder("Medallion inset", 2.8, 0.72, (0.0, 0.0, 14.45), dark_inlay)
add_torus("Medallion ring", 2.2, 0.42, (0.0, 0.0, 14.9), brass)
for x in (-16.0, 16.0):
    for y in (-10.0, 10.0):
        add_cylinder("Lid pin", 0.65, 0.45, (x, y, 14.0), brass, vertices=12)

# A small right-side winding stem and cross handle.
add_cylinder("Winding stem", 1.15, 5.8, (21.5, 0.0, 2.0), brass, rotation=(0.0, 1.5707963, 0.0))
add_cylinder("Winding collar", 2.0, 1.2, (19.0, 0.0, 2.0), brass, rotation=(0.0, 1.5707963, 0.0))
add_cylinder("Winding handle", 0.9, 7.2, (24.7, 0.0, 2.0), brass, rotation=(1.5707963, 0.0, 0.0))

# Two rear hinges make the fitted lid read as a functional keepsake.
for y in (-7.5, 7.5):
    add_cylinder("Hinge barrel", 1.0, 4.0, (0.0, y, 6.9), brass, rotation=(1.5707963, 0.0, 0.0))

# Put the object pivot at the base center and join the detailed pieces into one static mesh.
bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
base = parts[0]
bpy.context.view_layer.objects.active = base
bpy.ops.object.join()
base.name = "SM_BrassMusicBox"
base.data.name = "SM_BrassMusicBox"
for polygon in base.data.polygons:
    polygon.use_smooth = True

bpy.ops.object.select_all(action="DESELECT")
base.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "SM_BrassMusicBox.blend"))
bpy.ops.export_scene.fbx(
    filepath=str(FBX_PATH),
    use_selection=True,
    object_types={"MESH"},
    bake_anim=False,
    axis_forward="-Y",
    axis_up="Z",
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_UNITS",
    path_mode="RELATIVE",
    mesh_smooth_type="SMOOTH_GROUP",
    use_mesh_modifiers=True,
)

report = {
    "fbx": str(FBX_PATH),
    "blend": str(OUT / "SM_BrassMusicBox.blend"),
    "dimensions_cm": list(base.dimensions),
    "vertices": len(base.data.vertices),
    "faces": len(base.data.polygons),
    "material_slots": [slot.name for slot in base.data.materials],
}
(ROOT / "Saved/MansionConnection/Music_Box_Asset.json").write_text(json.dumps(report, indent=2))
print("BRASS_MUSIC_BOX_CREATED", json.dumps(report), flush=True)
