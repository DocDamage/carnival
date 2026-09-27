"""Prepare stable reference-pose FBXs and verify existing RamsterZ retargets."""
import json
import math
from pathlib import Path
import bpy
from io_scene_fbx import export_fbx_bin
from mathutils.kdtree import KDTree
from mathutils import Matrix, Vector

BASE=Path(r"F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Mobile")
OUT=BASE/'Unreal_Integration'
FBX=OUT/'FBX'
FBX.mkdir(parents=True,exist_ok=True)
original_writer=export_fbx_bin.fbx_data_object_elements
class ReferenceBone:
    def __init__(self,ob): self.ob=ob
    def __getattr__(self,n): return getattr(self.ob,n)
    def fbx_object_tx(self,scene_data,**kwargs): return self.ob.fbx_object_tx(scene_data,rest=True)
def write_model(root,ob,data): return original_writer(root,ReferenceBone(ob) if ob.is_bone else ob,data)
export_fbx_bin.fbx_data_object_elements=write_model

def coords(mesh):
    bpy.context.view_layer.update()
    ob=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); data=ob.to_mesh()
    points=[ob.matrix_world @ v.co for v in data.vertices]
    ob.to_mesh_clear()
    return points

def mesh_error(a,b):
    tree=KDTree(len(a))
    for i,v in enumerate(a): tree.insert(v,i)
    tree.balance()
    return max(tree.find(v)[2] for v in b)

bpy.ops.wm.open_mainfile(filepath=str(BASE/'Possessed_Doll_Mobile_RamsterZ_Retargeted.blend'))
if bpy.context.object and bpy.context.object.mode!='OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
rig=bpy.data.objects['Doll_Mobile_Rig']; mesh=bpy.data.objects['Possessed_Doll_Mobile']
scene=bpy.context.scene; scene.render.fps=30
# Unreal's Blender FBX importer removes this object wrapper, keeping the animated
# "root" bone as the true skeleton root so capsule root motion can be extracted.
rig.name='Armature'
rig.animation_data.action=None
for p in rig.pose.bones:
    p.location=(0,0,0); p.rotation_euler=(0,0,0); p.scale=(1,1,1)
rig.update_tag(); bpy.context.view_layer.update()
# Normalize game exports to centimeters, +X forward, with the floor root at the
# actor origin. All bone-local translation curves scale with the reference bones.
conversion=Matrix.Translation((24,0,0)) @ Matrix.Rotation(math.pi/2,4,'Z') @ Matrix.Scale(100,4)
for v in mesh.data.vertices: v.co=conversion @ v.co
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for bone in rig.data.edit_bones: bone.transform(conversion)
bpy.ops.object.mode_set(mode='OBJECT')
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag=strip.channelbag(slot)
                if not bag: continue
                for curve in bag.fcurves:
                    if curve.data_path.startswith('pose.bones[') and curve.data_path.endswith('.location'):
                        for key in curve.keyframe_points:
                            key.co.y*=100;key.handle_left.y*=100;key.handle_right.y*=100
for pb in rig.pose.bones: pb.custom_shape_scale_xyz=tuple(v*100 for v in pb.custom_shape_scale_xyz)
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
for ob in list(bpy.data.objects):
    if ob.type in ['CAMERA','LIGHT']:
        ob.matrix_world=conversion @ ob.matrix_world
        if ob.type=='CAMERA': ob.data.ortho_scale*=100;ob.data.clip_end*=100
rig.update_tag();bpy.context.view_layer.update()
expected={b.name for b in rig.data.bones if b.use_deform}
settings=dict(use_selection=True,add_leaf_bones=False,use_armature_deform_only=True,
              axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',path_mode='RELATIVE')
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); mesh.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(FBX/'SK_Doll.fbx'),object_types={'ARMATURE','MESH'},bake_anim=False,**settings)
mesh.select_set(False)
references={}; output=[]
actions=[a for a in bpy.data.actions if a.name.startswith('Doll_')]
for action in actions:
    rig.animation_data.action=action
    start,end=[int(v) for v in action.frame_range]
    scene.frame_start=start; scene.frame_end=end
    snapshots={}
    for f in sorted(set([start,(start+end)//2,end])):
        scene.frame_set(f); snapshots[f]=[v*.01 for v in coords(mesh)]
    references[action.name]=snapshots
    bpy.ops.export_scene.fbx(filepath=str(FBX/(action.name+'.fbx')),object_types={'ARMATURE'},
        bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0.0,**settings)
    output.append({'name':action.name,'frames':[start,end],'seconds':(end-start)/30,'file':str(FBX/(action.name+'.fbx'))})
rig.animation_data.action=bpy.data.actions['Doll_Idle_Possessed_Loop'];scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Possessed_Doll_Unreal.blend'))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX/'SK_Doll.fbx'),use_anim=False)
target=next(o for o in bpy.data.objects if o.type=='ARMATURE')
body=next(o for o in bpy.data.objects if o.type=='MESH')
assert {b.name for b in target.data.bones}==expected
for item in output:
    old=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=item['file'],use_anim=True,anim_offset=0)
    anim=next(o for o in bpy.data.objects if o not in old and o.type=='ARMATURE')
    target.animation_data_create();target.animation_data.action=anim.animation_data.action
    target.animation_data.action_slot=anim.animation_data.action_slot
    errors=[]
    for f,reference in references[item['name']].items():
        bpy.context.scene.frame_set(f)
        e=mesh_error(reference,coords(body));errors.append({'frame':f,'max_mesh_error_m':e})
    item['roundtrip_samples']=errors
    bpy.data.objects.remove(anim,do_unlink=True)
(OUT/'Prepared_Animation_Manifest.json').write_text(json.dumps(output,indent=2))
maximum=max(s['max_mesh_error_m'] for item in output for s in item['roundtrip_samples'])
assert maximum<.002,('FBX roundtrip exceeds 2 mm tolerance',maximum)
print('DOLL_UNREAL_FBX_VALIDATED',len(output),flush=True)
print('MAX_ROUNDTRIP_ERROR_METERS',maximum,flush=True)
