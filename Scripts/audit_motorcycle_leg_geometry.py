"""Compare sampled leg centerlines with actual assembled bike triangles.

Centerline intersections are definite geometric conflicts. Surface distances
are conservative diagnostics, not proof of full skinned-mesh clearance.
"""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

root=Path(r'F:\Carnival')
bpy.ops.wm.open_mainfile(filepath=str(root/'Content/Carnival/Vehicles/Motorcycle/Assembled/Source/CarnivalBike_Assembly.blend'))
trees={}
deps=bpy.context.evaluated_depsgraph_get()
for obj in bpy.context.scene.objects:
    if obj.type!='MESH': continue
    evaluated=obj.evaluated_get(deps)
    mesh=evaluated.to_mesh()
    vertices=[]
    for v in mesh.vertices:
        p=evaluated.matrix_world@v.co
        vertices.append((p.x,-p.y,p.z))
    trees[obj.name]=BVHTree.FromPolygons(vertices,[tuple(p.vertices) for p in mesh.polygons])
    evaluated.to_mesh_clear()
report={}
samples=json.loads((root/'Saved/DirtBike/Transition_Leg_Samples.json').read_text())
for name,frames in samples.items():
    hits=[]; closest={}
    for frame in frames:
        for side in ['l','r']:
            for a,b in [('thigh','calf'),('calf','foot'),('foot','ball')]:
                start=Vector(frame['bones'][a+'_'+side]); end=Vector(frame['bones'][b+'_'+side])
                delta=end-start
                key=a+'_'+side
                for part,tree in trees.items():
                    hit,normal,index,distance=tree.ray_cast(start,delta.normalized(),delta.length)
                    if hit is not None:
                        hits.append({'time':frame['time'],'fraction':frame['fraction'],'leg_segment':key,'bike_part':part,'point':list(hit)})
                    for i in range(math.ceil(delta.length/2)+1):
                        point=start+delta*(i/math.ceil(delta.length/2))
                        _,_,_,distance=tree.find_nearest(point)
                        if distance is not None and (key not in closest or distance<closest[key]['distance_cm']):
                            closest[key]={'distance_cm':distance,'time':frame['time'],'fraction':frame['fraction'],'bike_part':part,'point':list(point)}
    report[name]={'sample_count':len(frames),'centerline_intersections':hits,'nearest_surface':closest}
    print(name,'intersections',len(hits),'first',hits[:1])
(root/'Saved/DirtBike/Transition_Leg_Geometry.json').write_text(json.dumps(report,indent=2))
