"""Inspect the supplied 1M-polygon factory facade before Unreal placement."""
import bpy
import json
import math
from mathutils import Vector
from pathlib import Path

ROOT = Path(r"F:\Carnival")
FBX = ROOT / "Saved/IndustrialHospital/Source/Facade_1M_6x8K/FBX_1_mln_6x8K/FBX_1_mln_6x8K.fbx"
OUT = ROOT / "Saved/IndustrialHospital/Previews"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX), use_image_search=False, global_scale=1.0)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise RuntimeError("Facade FBX imported without mesh objects")

corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
minimum = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
maximum = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
center = (minimum + maximum) * 0.5
dimensions = maximum - minimum
max_dim = max(dimensions)
faces = sum(len(obj.data.polygons) for obj in meshes)
triangles = sum(max(0, len(poly.vertices) - 2) for obj in meshes for poly in obj.data.polygons)

mat = bpy.data.materials.new("PreviewConcrete")
mat.diffuse_color = (0.24, 0.27, 0.29, 1.0)
mat.use_nodes = True
principled = mat.node_tree.nodes.get("Principled BSDF")
principled.inputs["Base Color"].default_value = (0.24, 0.27, 0.29, 1.0)
principled.inputs["Roughness"].default_value = 0.85
for obj in meshes:
    obj.data.materials.clear()
    obj.data.materials.append(mat)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1440
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("FacadePreviewWorld")
scene.world.color = (0.045, 0.05, 0.06)
scene.render.resolution_percentage = 75

def add_area(name, position, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector(center) - obj.location).to_track_quat("-Z", "Y").to_euler()

add_area("Key", center + Vector((max_dim, -max_dim, max_dim)), 6000, max_dim * 0.8)
add_area("Fill", center + Vector((-max_dim, -max_dim * 0.25, max_dim * 0.45)), 3000, max_dim * 0.7)

camera_data = bpy.data.cameras.new("FacadePreviewCamera")
camera = bpy.data.objects.new("FacadePreviewCamera", camera_data)
scene.collection.objects.link(camera)
camera.data.type = "ORTHO"
camera.data.ortho_scale = max(dimensions.x, dimensions.y) * 1.25
scene.camera = camera

views = [
    ("Facade_Front.png", center + Vector((0, -max_dim * 1.8, dimensions.z * 0.25)), "-Y"),
    ("Facade_Left.png", center + Vector((-max_dim * 1.8, 0, dimensions.z * 0.25)), "-X"),
    ("Facade_Back.png", center + Vector((0, max_dim * 1.8, dimensions.z * 0.25)), "+Y"),
]
paths = []
for filename, position, direction in views:
    camera.location = position
    camera.rotation_euler = (Vector(center) - position).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)
    paths.append(str(OUT / filename))

report = {
    "fbx": str(FBX),
    "mesh_objects": len(meshes),
    "faces": faces,
    "triangles": triangles,
    "bounds_min": list(minimum),
    "bounds_max": list(maximum),
    "dimensions": list(dimensions),
    "views": paths,
}
(OUT / "Facade_Inspection.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2), flush=True)
