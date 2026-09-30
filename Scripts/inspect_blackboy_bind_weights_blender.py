"""Compare complete bone bind matrices and skin weighting in immutable/working FBX."""
import hashlib,json,math
from pathlib import Path
import bpy
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
source=OUT/'BlackBoy/fbx_clean/fbx Clean.fbx';prepared=OUT/'BlackBoy/Prepared/BlackBoy_Rigged.fbx'
REPORT={'success':False,'files':[],'limits':'Read-only bind/weight/deformed-reference comparison; no production re-rig or rendered acceptance.'}

def matrix(m):return [[float(v) for v in row] for row in m]

def inspect(path):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False,automatic_bone_orientation=False)
 rigs=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(rigs)==1
 rig=rigs[0];row={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bones':{},'meshes':{}}
 for bone in rig.data.bones:
  pose=rig.pose.bones[bone.name]
  row['bones'][bone.name]={'parent':bone.parent.name if bone.parent else None,
   'bind_world':matrix(rig.matrix_world@bone.matrix_local),'pose_world':matrix(rig.matrix_world@pose.matrix),
   'pose_basis':matrix(pose.matrix_basis),'head_world_m':list(rig.matrix_world@bone.head_local)}
 depsgraph=bpy.context.evaluated_depsgraph_get()
 for obj in bpy.data.objects:
  if obj.type!='MESH' or not any(m.type=='ARMATURE' and m.object==rig for m in obj.modifiers):continue
  groups={};vertices=[]
  for vertex in obj.data.vertices:
   point=obj.matrix_world@vertex.co;vertices.append(list(point))
   for entry in vertex.groups:
    name=obj.vertex_groups[entry.group].name
    bucket=groups.setdefault(name,{'weight_sum':0.,'weighted_center_m':[0.,0.,0.],'vertex_count':0})
    bucket['weight_sum']+=entry.weight;bucket['vertex_count']+=1
    for axis in range(3):bucket['weighted_center_m'][axis]+=point[axis]*entry.weight
  for name,g in groups.items():
   if g['weight_sum']>0:g['weighted_center_m']=[v/g['weight_sum'] for v in g['weighted_center_m']]
  evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh()
  posed=[list(evaluated.matrix_world@v.co) for v in mesh.vertices];evaluated.to_mesh_clear()
  assert len(vertices)==len(posed),obj.name
  row['meshes'][obj.name]={'vertices':vertices,'evaluated_reference_vertices':posed,'groups':groups,
   'shape_keys':[{'name':k.name,'value':float(k.value),'relative':k.relative_key.name} for k in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
   'armature_modifiers':[{'preserve_volume':m.use_deform_preserve_volume,'vertex_groups':m.use_vertex_groups,'envelopes':m.use_bone_envelopes,'vertex_group':m.vertex_group} for m in obj.modifiers if m.type=='ARMATURE']}
 return row

before=inspect(source);after=inspect(prepared)
assert before['bones'].keys()==after['bones'].keys() and before['meshes'].keys()==after['meshes'].keys()
errors={'bone_bind_world_matrix':0.,'bone_pose_world_matrix':0.,'pose_basis_matrix':0.,'raw_vertex_m':0.,'evaluated_reference_vertex_m':0.,'skin_weight_sum':0.}
for bone in before['bones']:
 for key,out in [('bind_world','bone_bind_world_matrix'),('pose_world','bone_pose_world_matrix'),('pose_basis','pose_basis_matrix')]:
  errors[out]=max(errors[out],max(abs(a-b) for x,y in zip(before['bones'][bone][key],after['bones'][bone][key]) for a,b in zip(x,y)))
for name,a in before['meshes'].items():
 b=after['meshes'][name];assert len(a['vertices'])==len(b['vertices'])
 for key,out in [('vertices','raw_vertex_m'),('evaluated_reference_vertices','evaluated_reference_vertex_m')]:
  errors[out]=max(errors[out],max(math.dist(x,y) for x,y in zip(a[key],b[key])))
 assert a['groups'].keys()==b['groups'].keys(),name
 errors['skin_weight_sum']=max(errors['skin_weight_sum'],max(abs(g['weight_sum']-b['groups'][group]['weight_sum']) for group,g in a['groups'].items()))
for row in (before,after):
 for mesh in row['meshes'].values():
  mesh['vertex_count']=len(mesh.pop('vertices'));mesh.pop('evaluated_reference_vertices')
REPORT.update(success=True,files=[before,after],maximum_errors=errors,
              prepared_bind_matches_source=all(v<.001 for v in errors.values()))
(OUT/'BlackBoy_Bind_Weights_Inspection.json').write_text(json.dumps(REPORT,indent=2))
print('Bind/weight comparison',errors)
