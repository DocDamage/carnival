"""Bake supplied motorcycle parts into forward-facing centimetre-space exports.

Preserves the source FBX. Body uses a single rigid bone; wheels stay separate
with axle-centred pivots for runtime rolling and steering.
"""
import json
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Content/Carnival/Vehicles/Motorcycle/Assembled/Source'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = .01
bpy.ops.import_scene.fbx(filepath=str(ROOT / 'Content/Carnival/Vehicles/Motorcycle/Mesh/SK_RSG_Bike.fbx'))
parts = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
# Read evaluated world coordinates before changing any object transforms.
coords = {obj.name: [obj.matrix_world @ vertex.co for vertex in obj.data.vertices] for obj in parts}
# FBX import into a centimetre scene rescales the source metres automatically.
raw_height = max(p.z for values in coords.values() for p in values)
unit_factor = 100. if raw_height < 10. else 1.
# The supplied model is oversized relative to its mannequin riding clip.
# Contact overlays put the pelvis at seat height at this uniform scale.
assembly_scale = .75
factor = unit_factor * assembly_scale
floor = min(p.z for values in coords.values() for p in values)
manifest = {'source': 'SK_RSG_Bike.fbx', 'unit_factor': unit_factor, 'assembly_scale': assembly_scale,
            'floor_shift_cm': -floor*factor, 'parts': []}
wheel_parts = []
body_parts = []
for obj in parts:
    values = coords[obj.name]
    is_wheel = 'Wheel' in obj.name
    center = Vector(tuple((min(p[i] for p in values)+max(p[i] for p in values))/2 for i in range(3))) if is_wheel else Vector()
    for vertex, world in zip(obj.data.vertices, values):
        p = world - center
        vertex.co = Vector((-p.y, p.x, p.z - (0. if is_wheel else floor))) * factor
    obj.matrix_world = Matrix.Identity(4)
    obj.data.update()
    # Blender's +Y becomes Unreal's -Y with this export/import basis.
    location = [-center.y*factor, -center.x*factor, (center.z-floor)*factor] if is_wheel else [0,0,0]
    record = {'original_name': obj.name, 'location_ue_cm': location,
              'materials': [slot.material.name if slot.material else None for slot in obj.material_slots]}
    if is_wheel:
        obj.name = 'SM_CarnivalBike_' + ('FrontWheel' if 'Front' in obj.name else 'RearWheel')
        record['wheel_radius_cm'] = (max(p.z for p in values)-min(p.z for p in values))*factor/2
        record['name'] = obj.name
        wheel_parts.append(obj)
    else:
        body_parts.append(obj)
    manifest['parts'].append(record)

def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

options = dict(use_selection=True, add_leaf_bones=False, axis_forward='-Y', axis_up='Z',
               apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', bake_anim=False,
               path_mode='RELATIVE')
for obj in wheel_parts:
    select([obj])
    bpy.ops.export_scene.fbx(filepath=str(OUT / (obj.name + '.fbx')), object_types={'MESH'}, **options)
# The supplied frame has no usable rider foot-rest surface at the riding
# position. Add a pair of compact tread blocks to the local derived assembly.
manifest['authored_footrests'] = []
for side in (-1, 1):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0,side*24,38))
    peg=bpy.context.object
    peg.name='Carnival_Footrest_'+('Left' if side>0 else 'Right')
    peg.scale=(4,8,1.5)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    material=next((slot.material for obj in body_parts for slot in obj.material_slots if slot.material),None)
    if material: peg.data.materials.append(material)
    body_parts.append(peg)
    manifest['authored_footrests'].append({'center_ue_cm':[0,-side*24,38], 'half_extent_cm':[4,8,1.5]})
select(body_parts)
bpy.ops.object.join()
body = bpy.context.object
body.name = 'SK_CarnivalBike_Body'
rig_data = bpy.data.armatures.new('CarnivalBikeRig')
rig = bpy.data.objects.new('Armature', rig_data)
bpy.context.collection.objects.link(rig)
select([rig])
bpy.ops.object.mode_set(mode='EDIT')
bone = rig_data.edit_bones.new('root')
bone.head = (0,0,0)
bone.tail = (0,10,0)
bpy.ops.object.mode_set(mode='OBJECT')
group = body.vertex_groups.new(name='root')
group.add(list(range(len(body.data.vertices))), 1., 'REPLACE')
modifier = body.modifiers.new('RigidBodySkin', 'ARMATURE')
modifier.object = rig
body.parent = rig
select([body,rig])
bpy.ops.export_scene.fbx(filepath=str(OUT / (body.name + '.fbx')), object_types={'MESH','ARMATURE'},
                          use_armature_deform_only=True, **options)
manifest['body'] = {'name': body.name, 'vertices': len(body.data.vertices),
                    'materials': [slot.material.name if slot.material else None for slot in body.material_slots]}
manifest['exports'] = [str(OUT / (obj.name + '.fbx')) for obj in [body, *wheel_parts]]
(OUT / 'Assembly_Manifest.json').write_text(json.dumps(manifest, indent=2))
for obj in wheel_parts:
    record = next(p for p in manifest['parts'] if p.get('name') == obj.name)
    x, y, z = record['location_ue_cm']
    obj.location = (x, -y, z)
    obj.parent = rig
    obj.color = (.055, .055, .06, 1.)
body.color = (.28, .32, .35, 1.)
bpy.ops.object.camera_add(location=(350, -480, 250))
camera = bpy.context.object
camera.rotation_euler = (Vector((0,0,85)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 390
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'OBJECT'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.background_type = 'WORLD'
scene.world = bpy.data.worlds.new('AssemblyPreviewWorld')
scene.world.color = (.12,.12,.12)
scene.render.resolution_x = 1200
scene.render.resolution_y = 850
scene.render.resolution_percentage = 100
preview = ROOT / 'Saved/DirtBike/Assembly_Source_Preview.png'
preview.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(preview)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'CarnivalBike_Assembly.blend'))
bpy.ops.render.render(write_still=True)
print(json.dumps(manifest, indent=2))
