"""Bake supplied default pose into a consistent bind on a separate working FBX.

Preserve every skinned mesh, vertex, weight and material slot. Check deformed
skin points before/after and verify the full exported bind/geometry round trip.
"""
import hashlib,json,math
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
OUT=Path(r'F:\Carnival\Saved\CharacterAcceptance\ChildSources')
source=OUT/'BlackBoy/fbx_clean/fbx Clean.fbx'
target=OUT/'BlackBoy/Prepared/BlackBoy_ConsistentBind.fbx'
bpy.ops.import_scene.fbx(filepath=str(source),use_anim=False,automatic_bone_orientation=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
assert len(meshes)==12

def posed_vertices(obj):
 depsgraph=bpy.context.evaluated_depsgraph_get();evaluated=obj.evaluated_get(depsgraph)
 mesh=evaluated.to_mesh();points=[list(evaluated.matrix_world@v.co) for v in mesh.vertices];evaluated.to_mesh_clear();return points

before={o.name:posed_vertices(o) for o in meshes}
object_transforms={o.name:o.matrix_world.copy() for o in meshes}
pose_world={b.name:rig.matrix_world@b.matrix.copy() for b in rig.pose.bones}
slots={o.name:[s.material.name if s.material else None for s in o.material_slots] for o in meshes}
weights={o.name:[[(o.vertex_groups[g.group].name,float(g.weight)) for g in v.groups] for v in o.data.vertices] for o in meshes}
# Body/eye/hair morphs require the same skin transform on every shape key,
# including Basis. Baking mesh.vertices alone does not change evaluated keys.
deformed_keys={};deformed_basis={};key_names={}
for obj in meshes:
 mod=next(m for m in obj.modifiers if m.type=='ARMATURE')
 assert not mod.use_deform_preserve_volume and mod.use_vertex_groups and not mod.use_bone_envelopes and not mod.vertex_group
 object_inverse=obj.matrix_world.inverted();rig_world=rig.matrix_world
 transforms={b.name:object_inverse@rig_world@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@rig_world.inverted()@obj.matrix_world for b in rig.data.bones}
 per_vertex=[]
 for groups in weights[obj.name]:
  active=[(transforms[n],w) for n,w in groups if n in transforms and w>0]
  if not active:per_vertex.append(Matrix.Identity(4));continue
  total=sum(w for _,w in active);tx=Matrix(((0.,)*4,)*4)
  for transform,weight in active:tx+=transform*(weight/total)
  per_vertex.append(tx)
 keys=list(obj.data.shape_keys.key_blocks) if obj.data.shape_keys else []
 assert not any(abs(k.value)>.0001 for k in keys)
 key_names[obj.name]=[(k.name,k.relative_key.name) for k in keys]
 deformed_keys[obj.name]={k.name:[tx@v.co for tx,v in zip(per_vertex,k.data)] for k in keys}
 basis=deformed_keys[obj.name][keys[0].name] if keys else [tx@v.co for tx,v in zip(per_vertex,obj.data.vertices)]
 deformed_basis[obj.name]=basis
 assert max(math.dist(list(obj.matrix_world@v),p) for v,p in zip(basis,before[obj.name]))<.0001,obj.name
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
for obj in meshes:
 for v,p in zip(obj.data.vertices,deformed_basis[obj.name]):v.co=p
 if obj.data.shape_keys:
  for key in obj.data.shape_keys.key_blocks:
   for v,p in zip(key.data,deformed_keys[obj.name][key.name]):v.co=p
 obj.data.update()
bpy.context.view_layer.update()
after={o.name:posed_vertices(o) for o in meshes}
skin_error=max(math.dist(a,b) for name in before for a,b in zip(before[name],after[name]))
bind_error=max(abs(a-b) for bone in rig.data.bones for ra,rb in zip(pose_world[bone.name],rig.matrix_world@bone.matrix_local) for a,b in zip(ra,rb))
assert skin_error<.0001,(skin_error,bind_error)
assert bind_error<.0001,bind_error
for obj in meshes:
 assert weights[obj.name]==[[(obj.vertex_groups[g.group].name,float(g.weight)) for g in v.groups] for v in obj.data.vertices]
assert max(abs(v-(1 if i==j else 0)) for bone in rig.pose.bones for i,row in enumerate(bone.matrix_basis) for j,v in enumerate(row))<.0001
bpy.ops.object.select_all(action='DESELECT')
for obj in meshes+[rig]:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE','MESH'},
 bake_anim=False,add_leaf_bones=False,use_armature_deform_only=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,use_mesh_modifiers=True)
consistent_bind={b.name:rig.matrix_world@b.matrix_local.copy() for b in rig.data.bones}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(target),use_anim=False,automatic_bone_orientation=False)
new_rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
new_meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert {o.name for o in new_meshes}==before.keys() and {b.name for b in new_rig.data.bones}==consistent_bind.keys()
roundtrip_skin=max(math.dist(a,b) for obj in new_meshes for a,b in zip(before[obj.name],posed_vertices(obj)))
roundtrip_bind=max(abs(a-b) for bone in new_rig.data.bones for ra,rb in zip(consistent_bind[bone.name],new_rig.matrix_world@bone.matrix_local) for a,b in zip(ra,rb))
for obj in new_meshes:
 assert len(obj.data.vertices)==len(before[obj.name])
 assert [s.material.name if s.material else None for s in obj.material_slots]==slots[obj.name]
 assert weights[obj.name]==[[(obj.vertex_groups[g.group].name,float(g.weight)) for g in v.groups] for v in obj.data.vertices]
 keys=list(obj.data.shape_keys.key_blocks) if obj.data.shape_keys else []
 assert [(k.name,k.relative_key.name) for k in keys]==key_names[obj.name],obj.name
 for key in keys:
  assert max(math.dist(list(obj.matrix_world@v.co),list(object_transforms[obj.name]@p)) for v,p in zip(key.data,deformed_keys[obj.name][key.name]))<.0001,(obj.name,key.name)
assert roundtrip_skin<.0001 and roundtrip_bind<.0001,(roundtrip_skin,roundtrip_bind)
report={'success':True,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'prepared_fbx':str(target),'prepared_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
 'mesh_count':len(new_meshes),'bone_count':len(new_rig.data.bones),'skin_error_m':skin_error,'bind_matrix_error':bind_error,
 'roundtrip_skin_error_m':roundtrip_skin,'roundtrip_bind_matrix_error':roundtrip_bind,
 'all_weights_preserved':True,'all_material_slots_preserved':True,
 'limits':'Consistent-bind working copy only. Import, retarget, clothing/gait/actor/ride acceptance remain separate.'}
(OUT/'BlackBoy_Consistent_Bind_FBX.json').write_text(json.dumps(report,indent=2))
print('Consistent bind verified:',report)
