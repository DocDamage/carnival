"""Import the verified centimeter FBXs, materials, and reusable doll animations.

Run with run_doll_tool.py unreal. Only assets in PossessedDoll are authored.
"""
import json
from pathlib import Path
import unreal

BASE='/Game/Carnival/Characters/PossessedDoll'
SOURCE=Path(r'F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Mobile')
OUT=Path(r'F:\Carnival\Saved\HauntedDollIntegration')
eal=unreal.EditorAssetLibrary
asset_tools=unreal.AssetToolsHelpers.get_asset_tools()
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')

def import_file(file,folder,name,options=None):
    path=folder+'/'+name
    if eal.does_asset_exist(path):
        existing=unreal.load_asset(path)
        if not isinstance(existing,(unreal.SkeletalMesh,unreal.AnimSequence)) or existing.get_editor_property('skeleton'):
            return existing
    task=unreal.AssetImportTask()
    task.filename=str(file);task.destination_path=folder;task.destination_name=name
    task.automated=True;task.save=True;task.replace_existing=True
    if options: task.options=options
    asset_tools.import_asset_tasks([task])
    # The legacy FBX task saves its primary object only; explicitly persist the
    # generated skeleton/physics dependencies before any subsequent imports.
    eal.save_directory(BASE,only_if_is_dirty=True,recursive=True)
    result=unreal.load_asset(path)
    assert result, (path,task.imported_object_paths)
    return result

def options(skeleton=None):
    opt=unreal.FbxImportUI()
    opt.automated_import_should_detect_type=False
    opt.import_as_skeletal=True;opt.import_mesh=skeleton is None
    opt.import_animations=skeleton is not None
    opt.import_materials=False;opt.import_textures=False
    opt.create_physics_asset=skeleton is None
    opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION if skeleton else unreal.FBXImportType.FBXIT_SKELETAL_MESH
    opt.skeleton=skeleton
    data=opt.anim_sequence_import_data if skeleton else opt.skeletal_mesh_import_data
    data.set_editor_property('convert_scene',True)
    data.set_editor_property('convert_scene_unit',True)
    data.set_editor_property('force_front_x_axis',False)
    if skeleton:
        data.set_editor_property('animation_length',unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
        data.set_editor_property('use_default_sample_rate',True)
    else:
        data.set_editor_property('update_skeleton_reference_pose',False)
        data.set_editor_property('use_t0_as_ref_pose',False)
    return opt

mesh=import_file(SOURCE/'Unreal_Integration/FBX/SK_Doll.fbx',BASE,'SK_Doll',options())
skeleton=mesh.skeleton
ref=skeleton.get_reference_pose()
names=ref.get_bone_names()
assert len(names)==26 and str(names[0])=='root',[str(n) for n in names]
root=ref.get_bone_pose('root',unreal.AnimPoseSpaces.WORLD)
assert abs(root.scale3d.x-1)<.001,str(root)

tex={}
for name in ['Doll_BaseColor','Doll_Legs_BaseColor','Doll_MetallicRoughness']:
    t=import_file(SOURCE/'Textures'/(name+'.png'),BASE+'/Materials', 'T_'+name)
    t.set_editor_property('srgb',name!='Doll_MetallicRoughness')
    if name=='Doll_MetallicRoughness': t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
    tex[name]=t;eal.save_loaded_asset(t)

mel=unreal.MaterialEditingLibrary
def material(name,base,metal=None):
    path=BASE+'/Materials/'+name
    if eal.does_asset_exist(path):return unreal.load_asset(path)
    m=asset_tools.create_asset(name,BASE+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    m.set_editor_property('two_sided',True)
    m.set_editor_property('used_with_skeletal_mesh',True)
    bc=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-400,-150)
    bc.set_editor_property('texture',tex[base])
    mel.connect_material_property(bc,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
    if metal:
        mr=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-400,150)
        mr.set_editor_property('texture',tex[metal]);mr.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        mel.connect_material_property(mr,'G',unreal.MaterialProperty.MP_ROUGHNESS)
        mel.connect_material_property(mr,'B',unreal.MaterialProperty.MP_METALLIC)
    else:
        rough=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-180,180)
        rough.set_editor_property('r',.62)
        mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(m);eal.save_loaded_asset(m)
    return m

body=material('M_Doll_Body','Doll_BaseColor','Doll_MetallicRoughness')
legs=material('M_Doll_Legs','Doll_Legs_BaseColor')
slots=list(mesh.materials)
for i,slot in enumerate(slots):
    slot.material_interface=legs if 'leg' in str(slot.material_slot_name).lower() else body
mesh.set_editor_property('materials',slots)
eal.save_loaded_asset(mesh)

manifest=json.loads((SOURCE/'Unreal_Integration/Prepared_Animation_Manifest.json').read_text())
report={'mesh':mesh.get_path_name(),'skeleton':skeleton.get_path_name(),
        'reference_pose':{str(n):str(ref.get_bone_pose(n,unreal.AnimPoseSpaces.WORLD)) for n in names},
        'material_slots':[str(s.material_slot_name) for s in slots], 'animations':[]}
for item in manifest:
    folder=BASE+'/Animations/'+('FreeGrim' if 'RamsterZ' in item['name'] else 'Original')
    a=import_file(item['file'],folder,item['name'],options(skeleton))
    assert isinstance(a,unreal.AnimSequence) and a.get_editor_property('skeleton')==skeleton,a
    use_root=item['name'].endswith('RootMotion') or item['name'] in ['Doll_Jumpscare_Lunge','Doll_Jump_InPlace']
    a.set_editor_property('enable_root_motion',use_root)
    a.set_editor_property('root_motion_root_lock',unreal.RootMotionRootLock.ANIM_FIRST_FRAME)
    a.set_editor_property('force_root_lock',not use_root and 'RamsterZ' not in item['name'])
    eal.save_loaded_asset(a)
    duration=a.get_editor_property('sequence_length')
    report['animations'].append({'name':a.get_name(),'path':a.get_path_name(),'seconds':duration,'root_motion':use_root,
        'root_start':str(unreal.AnimationLibrary.get_bone_pose_for_time(a,'root',0,False)),
        'root_end':str(unreal.AnimationLibrary.get_bone_pose_for_time(a,'root',duration,False))})
(OUT/'Imported_Doll.json').write_text(json.dumps(report,indent=2))
apis={}
for name in ['AnimPoseExtensions','AnimPoseEvaluationOptions','IKRetargeterController','IKRetargetFKChainsOpController','IKRetargetRootMotionOpController','IKRetargetPelvisMotionOpController']:
    cls=getattr(unreal,name,None)
    apis[name]={'doc':str(getattr(cls,'__doc__','')),'members':{m:str(getattr(cls,m).__doc__) for m in dir(cls) if not m.startswith('_') and any(t in m for t in ['pose','retarget','settings','chain','op_'])} if cls else {}}
(OUT/'Pose_API.json').write_text(json.dumps(apis,indent=2))
unreal.log_warning('DOLL_IMPORT_COMPLETE '+str(len(report['animations'])))
