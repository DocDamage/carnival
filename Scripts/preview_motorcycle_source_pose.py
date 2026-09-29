"""Render source riding-joint positions over the assembled supplied bike."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r'F:\Carnival')
source = ROOT / 'Content/Carnival/Vehicles/Motorcycle/Assembled/Source'
bpy.ops.wm.open_mainfile(filepath=str(source / 'CarnivalBike_Assembly.blend'))
manifest = json.loads((source / 'Assembly_Manifest.json').read_text())
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT / 'Content/Carnival/Vehicles/Motorcycle/Animations/Mounted/Idle/AS_Idle_Riding.fbx'))
rig = next(obj for obj in bpy.data.objects if obj not in before and obj.type == 'ARMATURE')
bpy.context.scene.frame_set(15)
names = ['pelvis','spine_01','spine_02','spine_03','neck_01','head',
         'clavicle_l','upperarm_l','lowerarm_l','hand_l','clavicle_r','upperarm_r','lowerarm_r','hand_r',
         'thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']
points = {}
for name in names:
    bone = rig.pose.bones.get(name)
    if not bone: continue
    point = rig.matrix_world @ bone.head
    points[name] = Vector((-point.y, point.x, point.z + manifest['floor_shift_cm']))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=2.2, location=points[name])
    bpy.context.object.color = (1.,.24,.025,1.)
for name in names:
    bone = rig.pose.bones.get(name)
    if not bone or not bone.parent or bone.parent.name not in points: continue
    a, b = points[name], points[bone.parent.name]
    delta = b-a
    if delta.length < .1: continue
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=1.15, depth=delta.length, location=(a+b)/2)
    bpy.context.object.rotation_euler = delta.to_track_quat('Z','Y').to_euler()
    bpy.context.object.color = (1.,.24,.025,1.)
out = ROOT / 'Saved/DirtBike'
(out / 'Source_Rider_Contact.json').write_text(json.dumps({name:list(point) for name,point in points.items()}, indent=2))
bpy.context.scene.render.filepath = str(out / 'Source_Rider_Contact.png')
bpy.ops.render.render(write_still=True)
bike_rig = next(obj for obj in before if obj.type == 'ARMATURE')
variant = .75 / manifest.get('assembly_scale', 1.)
bike_rig.scale = (variant, variant, variant)
bpy.context.scene.render.filepath = str(out / 'Source_Rider_Contact_Bike75.png')
bpy.ops.render.render(write_still=True)
