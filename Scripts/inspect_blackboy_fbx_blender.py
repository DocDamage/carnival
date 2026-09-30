"""Read the supplied fourth child's FBX rig/material slots without rewriting it."""
import json
from pathlib import Path
import bpy

ROOT=Path(r'F:\Carnival');BASE=ROOT/'Saved/CharacterAcceptance/ChildSources'
source=BASE/'BlackBoy/fbx_clean/fbx Clean.fbx'
bpy.ops.import_scene.fbx(filepath=str(source),use_anim=False,automatic_bone_orientation=False)
report={'success':False,'source':str(source),'meshes':[],'armatures':[],
    'texture_files':[str(x) for x in (BASE/'BlackBoy/textures').rglob('*') if x.is_file()],
    'limits':'Read-only source inspection. Does not establish Unreal import, animation, clothing appearance or actor fitting.'}
for obj in bpy.data.objects:
    if obj.type=='MESH':
        points=[obj.matrix_world@v.co for v in obj.data.vertices]
        report['meshes'].append({'name':obj.name,'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons),
            'bounds_m':[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]],
            'materials':[slot.material.name if slot.material else None for slot in obj.material_slots],
            'armatures':[m.object.name for m in obj.modifiers if m.type=='ARMATURE' and m.object]})
    elif obj.type=='ARMATURE':
        report['armatures'].append({'name':obj.name,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,
            'head_m':list(obj.matrix_world@b.head_local),'tail_m':list(obj.matrix_world@b.tail_local)} for b in obj.data.bones]})
report['success']=bool(report['meshes']) and bool(report['armatures'])
(BASE/'BlackBoy_FBX_Inspection.json').write_text(json.dumps(report,indent=2))
print('BlackBoy FBX:',len(report['meshes']),'meshes;',len(report['armatures']),'armatures')
