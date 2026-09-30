"""Export a working FBX containing all rigged meshes, excluding only the helper Cube.

Original FBX is immutable. A fresh round-trip import checks mesh counts, world
bounds, material slots and bone positions before this copy can be used in UE.
"""
import hashlib,json,math
from pathlib import Path
import bpy

BASE=Path(r'F:\Carnival\Saved\CharacterAcceptance\ChildSources')
source=BASE/'BlackBoy/fbx_clean/fbx Clean.fbx'
out=BASE/'BlackBoy/Prepared';out.mkdir(parents=True,exist_ok=True)
target=out/'BlackBoy_Rigged.fbx'
bpy.ops.import_scene.fbx(filepath=str(source),use_anim=False,automatic_bone_orientation=False)
rigs=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(rigs)==1
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rigs[0] for m in o.modifiers)]
excluded=[o for o in bpy.data.objects if o.type=='MESH' and o not in meshes]
assert len(meshes)==12 and len(excluded)==1 and excluded[0].name=='Cube'

def inventory(objects,rig):
    rows={}
    for obj in objects:
        points=[obj.matrix_world@v.co for v in obj.data.vertices]
        rows[obj.name]={'vertices':len(points),'bounds_m':[[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]],
            'materials':[s.material.name if s.material else None for s in obj.material_slots]}
    return {'meshes':rows,'bones':{b.name:list(rig.matrix_world@b.head_local) for b in rig.data.bones}}

before=inventory(meshes,rigs[0]);bpy.ops.object.select_all(action='DESELECT')
for obj in meshes+rigs: obj.select_set(True)
bpy.context.view_layer.objects.active=rigs[0]
bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE','MESH'},
    bake_anim=False,add_leaf_bones=False,use_armature_deform_only=False,
    axis_forward='-Z',axis_up='Y',apply_unit_scale=True,use_mesh_modifiers=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(target),use_anim=False,automatic_bone_orientation=False)
new_rigs=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(new_rigs)==1
after=inventory([o for o in bpy.data.objects if o.type=='MESH'],new_rigs[0])
assert set(before['meshes'])==set(after['meshes']) and set(before['bones'])==set(after['bones'])
maximum=0
for name,row in before['meshes'].items():
    actual=after['meshes'][name]
    assert row['vertices']==actual['vertices'] and row['materials']==actual['materials'],name
    maximum=max(maximum,*(abs(a-b) for left,right in zip(row['bounds_m'],actual['bounds_m']) for a,b in zip(left,right)))
for name,point in before['bones'].items(): maximum=max(maximum,math.dist(point,after['bones'][name]))
assert maximum<.001,maximum
report={'success':True,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'prepared_fbx':str(target),'prepared_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'excluded':['Cube (unskinned helper)'],'inventory':after,'max_roundtrip_error_m':maximum,
    'limits':'Prepared FBX only. Unreal import, material binding, retargeting and rendered/actor acceptance remain required.'}
(BASE/'BlackBoy_Prepared_FBX.json').write_text(json.dumps(report,indent=2))
print('Verified prepared child FBX:',len(after['meshes']),'meshes,',len(after['bones']),'bones; error',maximum,'m')
