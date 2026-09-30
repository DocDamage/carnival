"""Import the verified working FBX and supplied PBR maps into its own namespace.

Run through run_editor_authoring_guarded.py. Original licensed files are read-only.
This establishes import/material references; rendered and animation checks follow.
"""
import hashlib, json, math, traceback
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
SOURCE = ROOT/'Saved/CharacterAcceptance/ChildSources'
BASE = '/Game/Carnival/Characters/Children/BlackBoy'
REPORT = {'success': False, 'errors': [], 'materials': [], 'textures': [],
          'limits': 'Saved import and supplied material bindings only. No rendered, locomotion, seat or actor acceptance.'}
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

def import_asset(file, folder, name, options=None):
    path = folder+'/'+name
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    task = unreal.AssetImportTask()
    task.filename = str(file)
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = False
    if options:
        task.options = options
    tools.import_asset_tasks([task])
    eal.save_directory(BASE, only_if_is_dirty=True, recursive=True)
    asset = unreal.load_asset(path)
    assert asset, (path, list(task.imported_object_paths))
    return asset

def constant(material, value, prop):
    expression = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -180, 250)
    expression.set_editor_property('r', value)
    assert mel.connect_material_property(expression, '', prop)

texture_files = {}
for file in (SOURCE/'BlackBoy/textures').rglob('*'):
    if file.suffix.lower() not in ('.png', '.jpg', '.tga'):
        continue
    if file.stem in texture_files:
        raise RuntimeError('Ambiguous supplied texture '+file.stem)
    texture_files[file.stem] = file

def texture(stem, normal=False, color=False):
    file = texture_files.get(stem)
    if not file:
        return None
    asset = import_asset(file, BASE+'/Textures', 'T_'+stem)
    assert isinstance(asset, unreal.Texture2D)
    asset.set_editor_property('srgb', color)
    if normal:
        asset.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
    elif not color:
        asset.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    eal.save_loaded_asset(asset)
    REPORT['textures'].append({'asset': asset.get_path_name(), 'source': str(file),
                              'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                              'normal': normal, 'srgb': color})
    return asset

def connect_texture(material, stem, prop, normal=False, color=False, channel='RGB'):
    asset = texture(stem, normal, color)
    if not asset:
        return False
    expr = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -500, len(REPORT['textures'])*50)
    expr.set_editor_property('texture', asset)
    sampler = (unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else
               unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if color else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    expr.set_editor_property('sampler_type', sampler)
    assert mel.connect_material_property(expr, channel, prop)
    return True

try:
    prepared = json.loads((SOURCE/'BlackBoy_Prepared_FBX.json').read_text())
    assert prepared['success']
    file = Path(prepared['prepared_fbx'])
    assert hashlib.sha256(file.read_bytes()).hexdigest() == prepared['prepared_sha256']
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, 'Interchange.FeatureFlags.Import.FBX 0')
    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_as_skeletal = True
    options.import_mesh = True
    options.import_animations = False
    options.import_materials = False
    options.import_textures = False
    options.create_physics_asset = True
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    data = options.skeletal_mesh_import_data
    data.set_editor_property('convert_scene', True)
    data.set_editor_property('convert_scene_unit', True)
    data.set_editor_property('force_front_x_axis', False)
    data.set_editor_property('import_morph_targets', True)
    data.set_editor_property('update_skeleton_reference_pose', False)
    data.set_editor_property('use_t0_as_ref_pose', False)
    mesh = import_asset(file, BASE, 'SK_BlackBoy', options)
    assert isinstance(mesh, unreal.SkeletalMesh) and mesh.skeleton
    pose = mesh.skeleton.get_reference_pose()
    bones = [str(n) for n in pose.get_bone_names()]
    expected = set(prepared['inventory']['bones'])
    assert expected.issubset(bones), expected-set(bones)
    assert not set(bones)-expected-{'Armature'}, set(bones)-expected
    for bone in bones:
        tx = pose.get_bone_pose(bone, unreal.AnimPoseSpaces.WORLD)
        assert all(math.isfinite(x) for x in tx.translation.to_tuple()+tx.scale3d.to_tuple()), bone
    slots = list(mesh.materials)
    expected_slots = {name for obj in prepared['inventory']['meshes'].values() for name in obj['materials']}
    actual_slots = {str(slot.material_slot_name) for slot in slots}
    assert actual_slots == expected_slots, (actual_slots, expected_slots)
    for slot in slots:
        name = str(slot.material_slot_name)
        path = BASE+'/Materials/M_'+name
        material = unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(
            'M_'+name, BASE+'/Materials', unreal.Material, unreal.MaterialFactoryNew())
        assert isinstance(material, unreal.Material)
        mel.delete_all_material_expressions(material)
        material.set_editor_property('used_with_skeletal_mesh', True)
        masked = name in {'Hair_Transparency', 'Scalp_Transparency', 'Std_Eyelash', 'Shoes'}
        clear = name.startswith('Std_Cornea') or name.startswith('Std_Tearline')
        material.set_editor_property('two_sided', masked or clear)
        material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT if clear else
                                     unreal.BlendMode.BLEND_MASKED if masked else unreal.BlendMode.BLEND_OPAQUE)
        if clear:
            constant(material, .08 if name.startswith('Std_Cornea') else .12, unreal.MaterialProperty.MP_OPACITY)
            constant(material, .04, unreal.MaterialProperty.MP_ROUGHNESS)
            constant(material, 1.0, unreal.MaterialProperty.MP_BASE_COLOR)
        else:
            assert connect_texture(material, name+'_Diffuse', unreal.MaterialProperty.MP_BASE_COLOR, color=True)
            connect_texture(material, name+'_Normal', unreal.MaterialProperty.MP_NORMAL, normal=True)
            if not connect_texture(material, name+'_roughness', unreal.MaterialProperty.MP_ROUGHNESS, channel='R'):
                constant(material, .6, unreal.MaterialProperty.MP_ROUGHNESS)
            connect_texture(material, name+'_metallic', unreal.MaterialProperty.MP_METALLIC, channel='R')
            connect_texture(material, name+'_ao', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, channel='R')
            if masked:
                assert connect_texture(material, name+'_Opacity', unreal.MaterialProperty.MP_OPACITY_MASK, channel='R')
                material.set_editor_property('opacity_mask_clip_value', .333)
        mel.recompile_material(material)
        eal.save_loaded_asset(material)
        slot.material_interface = material
        REPORT['materials'].append({'slot': name, 'material': path, 'masked': masked, 'clear_surface': clear})
    mesh.set_editor_property('materials', slots)
    eal.save_loaded_asset(mesh)
    eal.save_directory(BASE, only_if_is_dirty=True, recursive=True)
    REPORT.update({'success': True, 'mesh': mesh.get_path_name(), 'skeleton': mesh.skeleton.get_path_name(),
                   'bone_count': len(bones), 'bones': bones, 'material_slot_count': len(slots),
                   'prepared_sha256': prepared['prepared_sha256']})
except Exception:
    REPORT['errors'].append(traceback.format_exc())
finally:
    (SOURCE/'BlackBoy_Unreal_Import.json').write_text(json.dumps(REPORT, indent=2))
