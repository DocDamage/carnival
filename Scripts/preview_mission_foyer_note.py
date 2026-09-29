"""Render a clean asset preview of Eli's physical foyer note."""

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(r"F:\Carnival")
SOURCE = ROOT / "Saved/MissionAuthoring/Source/FBX/SM_EliFoyerNote.blend"
OUTPUT = ROOT / "Saved/MissionAuthoring/SM_EliFoyerNote_Preview.png"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1200
scene.render.resolution_y = 850
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.filepath = str(OUTPUT)
scene.view_settings.view_transform = "AgX"
scene.render.image_settings.color_mode = "RGBA"
scene.render.resolution_percentage = 100

note = bpy.data.objects.get("SM_EliFoyerNote")
if note is None:
    raise RuntimeError("SM_EliFoyerNote mesh is missing from its Blender source")
for obj in scene.objects:
    if obj != note and obj.type == "MESH":
        obj.hide_render = True

floor_mat = bpy.data.materials.new("Preview_Floor")
floor_mat.diffuse_color = (0.055, 0.068, 0.075, 1.0)
bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0.0, 0.0, -0.13))
floor = bpy.context.object
floor.name = "Preview floor"
floor.data.materials.append(floor_mat)

world = scene.world or bpy.data.worlds.new("Preview World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.08, 0.09, 0.10, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25

def add_area(name, location, energy, size, color):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    lamp = bpy.data.objects.new(name, data)
    scene.collection.objects.link(lamp)
    lamp.location = location
    lamp.rotation_euler = (Vector((0.0, 0.0, 0.0)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
    return lamp

add_area("Key", (-8.0, -5.0, 16.0), 2200.0, 10.0, (1.0, 0.82, 0.60))
add_area("Fill", (8.0, 6.0, 12.0), 900.0, 8.0, (0.63, 0.78, 1.0))

camera_data = bpy.data.cameras.new("Note Preview Camera")
camera = bpy.data.objects.new("Note Preview Camera", camera_data)
scene.collection.objects.link(camera)
camera.location = (11.0, -15.0, 24.0)
camera.rotation_euler = (Vector((0.0, 0.0, 0.08)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera_data.type = "ORTHO"
camera_data.ortho_scale = 23.5
scene.camera = camera
scene.render.filepath = str(OUTPUT)
bpy.ops.render.render(write_still=True)
print("FOYER_NOTE_PREVIEW", OUTPUT, flush=True)
