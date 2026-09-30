"""Compare supplied default-pose skin normals with the consistent-bind copy."""
import json,math
from pathlib import Path
import bpy
OUT=Path(r'F:\Carnival\Saved\CharacterAcceptance\ChildSources')
REPORT={'success':False,'meshes':[],'limits':'Read-only evaluated corner-normal comparison; no asset repair or rendered acceptance.'}

def inspect(path):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False,automatic_bone_orientation=False)
 graph=bpy.context.evaluated_depsgraph_get();result={}
 for obj in bpy.data.objects:
  if obj.type!='MESH' or not any(m.type=='ARMATURE' for m in obj.modifiers):continue
  evaluated=obj.evaluated_get(graph);mesh=evaluated.to_mesh()
  transform=evaluated.matrix_world.to_3x3().inverted().transposed()
  result[obj.name]=[(transform@n.vector).normalized().copy() for n in mesh.corner_normals]
  evaluated.to_mesh_clear()
 return result

source=inspect(OUT/'BlackBoy/fbx_clean/fbx Clean.fbx')
candidate=inspect(OUT/'BlackBoy/Prepared/BlackBoy_ConsistentBind.fbx')
assert source.keys()==candidate.keys()
for name,a in source.items():
 b=candidate[name];assert len(a)==len(b),name
 angles=[math.degrees(math.acos(max(-1,min(1,x.dot(y))))) for x,y in zip(a,b)]
 REPORT['meshes'].append({'name':name,'corners':len(a),'maximum_error_degrees':max(angles),'mean_error_degrees':sum(angles)/len(angles),'corners_over_5_degrees':sum(x>5 for x in angles)})
REPORT['success']=True
(OUT/'BlackBoy_Bind_Normal_Inspection.json').write_text(json.dumps(REPORT,indent=2))
print('Normal comparison',REPORT['meshes'])
