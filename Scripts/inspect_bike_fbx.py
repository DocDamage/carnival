"""Read source motorcycle part bounds and skeletons in Blender; no source edits."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

root = Path(r'F:\Carnival')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(root / 'Content/Carnival/Vehicles/Motorcycle/Mesh/SK_RSG_Bike.fbx'))
report = {'objects': []}
for obj in bpy.context.scene.objects:
    entry = {'name': obj.name, 'type': obj.type, 'location': list(obj.location),
             'rotation': list(obj.rotation_euler), 'scale': list(obj.scale)}
    if obj.type == 'MESH':
        coords = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
        entry['world_min'] = [min(v[i] for v in coords) for i in range(3)]
        entry['world_max'] = [max(v[i] for v in coords) for i in range(3)]
        entry['vertices'] = len(obj.data.vertices)
    if obj.type == 'ARMATURE':
        entry['bones'] = [{'name': b.name, 'head': list(obj.matrix_world @ b.head_local),
                           'parent': b.parent.name if b.parent else None} for b in obj.data.bones]
    report['objects'].append(entry)
bpy.ops.import_scene.fbx(filepath=str(root / 'Content/Carnival/Vehicles/Motorcycle/Animations/Mounted/Idle/AS_Idle_Riding.fbx'))
bpy.context.scene.frame_set(15)
report['idle_armatures'] = []
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        report['idle_armatures'].append({'name': obj.name, 'scale': list(obj.scale),
            'bones': [{'name': bone.name, 'head': list(obj.matrix_world @ bone.head),
                       'tail': list(obj.matrix_world @ bone.tail)} for bone in obj.pose.bones]})
out = root / 'Saved/DirtBike'
out.mkdir(parents=True, exist_ok=True)
(out / 'Source_Bike_Inspection.json').write_text(json.dumps(report, indent=2))
print('SOURCE_BIKE_INSPECTION_COMPLETE')
