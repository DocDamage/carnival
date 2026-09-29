"""Measure supplied motorcycle contact geometry in assembled UE centimetres."""
import json
from pathlib import Path
import bpy
from mathutils import Vector
root=Path(r'F:\Carnival')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.scale_length=.01
bpy.ops.import_scene.fbx(filepath=str(root/'Content/Carnival/Vehicles/Motorcycle/Mesh/SK_RSG_Bike.fbx'))
rows=[]
for obj in bpy.context.scene.objects:
    if obj.type!='MESH': continue
    points=[obj.matrix_world@v.co for v in obj.data.vertices]
    points=[Vector((-p.y*.75,-p.x*.75,p.z*.75+2.195294)) for p in points]
    row={'name':obj.name,'bounds':[[min(p[i] for p in points) for i in range(3)],
                                 [max(p[i] for p in points) for i in range(3)]]}
    if obj.name=='SK_rsg_LastGuns_bike_01':
        row['grip_vertices']=[list(p) for p in points if abs(p.y)>35 and p.z>105]
        row['peg_vertices']=[list(p) for p in points if abs(p.y)>16 and p.z<60 and p.x<20]
    if 'rudder' in obj.name.lower() or 'equipment' in obj.name.lower():
        row['lateral_extremes']=[list(p) for p in sorted(points,key=lambda p:abs(p.y),reverse=True)[:24]]
    rows.append(row)
(root/'Saved/DirtBike/Contact_Geometry.json').write_text(json.dumps(rows,indent=2))
