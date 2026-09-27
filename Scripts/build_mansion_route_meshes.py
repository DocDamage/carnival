"""Author the continuous gravel approaches and timber rail-trail deck in Blender."""
import bpy,sys,math,json,bisect,random
from pathlib import Path
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import OUT,SECTIONS,distance,route_manifest
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
export=OUT/'Source/FBX';export.mkdir(parents=True,exist_ok=True)
settings=dict(use_selection=True,object_types={'MESH'},bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',path_mode='RELATIVE',use_mesh_modifiers=True,mesh_smooth_type='FACE')
mats={name:bpy.data.materials.new(name) for name in ['Gravel','Shoulder','Timber']}
manifest=[]
def save_mesh(name,verts,faces,slots,face_slots):
    # Unreal uses the opposite Y handedness; retain centimetre coordinates.
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(v[0],-v[1],v[2]) for v in verts],[],[tuple(reversed(f)) for f in faces]);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    for slot in slots:mesh.materials.append(mats[slot])
    for poly,index in zip(mesh.polygons,face_slots):poly.material_index=index
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for idx in poly.loop_indices:
            v=mesh.vertices[mesh.loops[idx].vertex_index].co
            uv.data[idx].uv=(v.x/200,v.y/200)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(export/(name+'.fbx')),**settings)
    manifest.append({'name':name,'vertices':len(verts),'faces':len(faces),'slots':slots,'bounds_min':[min(v[i] for v in verts) for i in range(3)],'bounds_max':[max(v[i] for v in verts) for i in range(3)]})
    return obj

# An asymmetric import check catches unit or handedness errors before placement.
save_mesh('SM_RouteImportProbe',[(900,1800,250),(1100,1800,250),(1100,2200,250),(900,2200,250),(900,1800,350),(1100,1800,350),(1100,2200,350),(900,2200,350)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],['Gravel'],[0]*6)
for section in SECTIONS:
    pts=section['points'];lengths=[0]
    for p,q in zip(pts,pts[1:]):lengths.append(lengths[-1]+distance(p,q))
    def at(s):
        i=min(len(pts)-2,max(0,bisect.bisect_right(lengths,s)-1));alpha=(s-lengths[i])/(lengths[i+1]-lengths[i])
        p=tuple(pts[i][k]*(1-alpha)+pts[i+1][k]*alpha for k in range(3))
        dx=pts[i+1][0]-pts[i][0];dy=pts[i+1][1]-pts[i][1];d=math.hypot(dx,dy)
        return p,(-dy/d,dx/d)
    chunk_size=3000 if section['surface']=='timber' else 4000
    chunks=math.ceil(lengths[-1]/chunk_size)
    for chunk in range(chunks):
        begin=chunk*lengths[-1]/chunks;end=(chunk+1)*lengths[-1]/chunks
        verts=[];faces=[];indices=[]
        if section['surface']=='gravel':
            profile=[(-740,-62),(-360,-14),(-230,0),(0,3),(230,0),(360,-14),(740,-62)]
            rows=math.ceil((end-begin)/150)+1
            for r in range(rows):
                s=begin+(end-begin)*r/(rows-1);p,n=at(s)
                for offset,z in profile:verts.append((p[0]+n[0]*offset,p[1]+n[1]*offset,p[2]+z))
            for r in range(rows-1):
                for c in range(len(profile)-1):
                    j=r*len(profile)+c;faces.append((j,j+len(profile),j+len(profile)+1,j+1));indices.append(0 if 1<=c<=4 else 1)
            slots=['Gravel','Shoulder']
        else:
            plank_count=math.ceil((end-begin)/28)
            for j in range(plank_count):
                s0=begin+(end-begin)*j/plank_count;s1=begin+(end-begin)*(j+1)/plank_count
                p0,n0=at(s0);p1,n1=at(s1-.35)
                zvar=(j%5-2)*.07
                base=len(verts)
                for dz in [-9,zvar]:
                    for p,n,side in [(p0,n0,-1),(p0,n0,1),(p1,n1,1),(p1,n1,-1)]:
                        verts.append((p[0]+n[0]*side*140,p[1]+n[1]*side*140,p[2]+dz))
                faces.extend([tuple(base+k for k in face) for face in [(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(0,1,2,3)]])
                indices.extend([0]*6)
            # Flush underside of the narrow seams provides uninterrupted wheel contact.
            rows=math.ceil((end-begin)/150)+1;base=len(verts)
            for r in range(rows):
                p,n=at(begin+(end-begin)*r/(rows-1))
                for side in [-1,1]:verts.append((p[0]+n[0]*side*140,p[1]+n[1]*side*140,p[2]-.7))
            for r in range(rows-1):
                j=base+r*2;faces.append((j,j+2,j+3,j+1));indices.append(0)
            slots=['Timber']
        save_mesh('SM_'+section['name']+'_'+str(chunk+1).zfill(2),verts,faces,slots,indices)
(OUT/'Route_Meshes.json').write_text(json.dumps(manifest,indent=2))
(OUT/'Route_Layout.json').write_text(json.dumps(route_manifest(),indent=2))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Source/Mansion_Coastal_Route.blend'))
print('ROUTE_MESHES_CREATED',len(manifest),flush=True)
