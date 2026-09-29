"""Project-only skin sampler repair. Run in editor; saves explicit packages only.

Copies the crowd master and only affected function ancestors. Twelve verified
non-virtual wrap samples use Shared:Wrap; texture-object-driven samples stay as
authored. Existing collections are backed up byte-for-byte before modification.
"""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
OUT = ROOT / 'Saved/CharacterRepairs'
BACKUP = OUT / ('CrowdSamplerBackup_' + STAMP)
REPORT = {'started': STAMP, 'backups': [], 'cloned_assets': [], 'changed_samples': [],
          'reparented_instances': [], 'preserved_embedded_parent_links': [],
          'pipeline_overrides': [], 'unresolved_pipeline_overrides': [],
          'saved_packages': [], 'errors': [], 'status': 'not_started'}
SOURCE_MASTER = '/MetaHumanCrowd/Materials/M_skin_unified_baked_crowd.M_skin_unified_baked_crowd'
LOCAL = '/Game/Carnival/Crowd/Materials/SamplerRepair'
TARGET_FUNCTIONS = {
    '/MetaHumanCharacter/Lookdev_UHM/Skin/Material_Functions/MF_skin_microSkinDetails.MF_skin_microSkinDetails',
    '/MetaHumanCharacter/Lookdev_UHM/Skin/Material_Functions/MF_skin_bentNormalsAO.MF_skin_bentNormalsAO',
    '/MetaHumanCharacter/Lookdev_UHM/Skin/Material_Functions/MF_Skin_ScalableNormals.MF_Skin_ScalableNormals',
    '/MetaHumanCharacter/Lookdev_UHM/Skin/Material_Functions/BakedGroomTextures/MF_BakedGroomTextures.MF_BakedGroomTextures',
}
ML = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
clones = {}
graph_assets = {}
edges = {}
backed_up = set()


def path(obj):
    return obj.get_path_name() if obj else None


def expressions(asset):
    if isinstance(asset, unreal.Material):
        return ML.get_material_expressions(asset)
    if isinstance(asset, unreal.MaterialFunction):
        return ML.get_material_function_expressions(asset)
    raise RuntimeError('Unsupported function type: ' + path(asset))


def backup(package):
    package = package.split('.')[0]
    if package in backed_up:
        return
    if not package.startswith('/Game/'):
        raise RuntimeError('Refusing non-project package mutation: ' + package)
    backed_up.add(package)
    relative = package[len('/Game/'):]
    for extension in ('.uasset', '.uexp', '.ubulk'):
        source = ROOT / 'Content' / (relative + extension)
        if source.exists():
            destination = BACKUP / (relative + extension)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            REPORT['backups'].append({'package': package, 'file': str(destination),
                                      'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})


def inspect_graph(asset):
    key = path(asset)
    if key in graph_assets:
        return
    graph_assets[key] = asset
    edges[key] = []
    for expression in expressions(asset):
        if isinstance(expression, unreal.MaterialExpressionMaterialFunctionCall):
            child = expression.get_editor_property('material_function')
            if child:
                edges[key].append(path(child))
                inspect_graph(child)


def affected(key, stack=None):
    stack = set() if stack is None else stack
    if key in TARGET_FUNCTIONS:
        return True
    if key in stack:
        return False
    return any(affected(child, stack | {key}) for child in edges[key])


def eligible(expression):
    if not isinstance(expression, unreal.MaterialExpressionTextureSample):
        return False
    # TextureObjectParameter inherits TextureSample, but does not sample itself.
    if 'TextureObject' in expression.get_class().get_name():
        return False
    if expression.get_editor_property('sampler_source') != unreal.SamplerSourceMode.SSM_FROM_TEXTURE_ASSET:
        return False
    texture = expression.get_editor_property('texture')
    if not texture or texture.get_editor_property('virtual_texture_streaming'):
        return False
    return (texture.get_editor_property('address_x') == unreal.TextureAddress.TA_WRAP
            and texture.get_editor_property('address_y') == unreal.TextureAddress.TA_WRAP
            and texture.get_editor_property('filter') == unreal.TextureFilter.TF_DEFAULT)


def duplicate(source, category):
    destination = LOCAL + '/' + category + '/' + source.get_name()
    if AL.does_asset_exist(destination):
        # Re-run only our own previously-created repair assets.
        backup(destination)
        result = unreal.load_asset(destination)
    else:
        result = AL.duplicate_asset(path(source), destination)
    if not result:
        raise RuntimeError('Could not create local copy: ' + destination)
    REPORT['cloned_assets'].append({'source': path(source), 'local': path(result)})
    return result


def clone_graph(key):
    if key in clones:
        return clones[key]
    if not affected(key):
        return graph_assets[key]
    result = duplicate(graph_assets[key], 'Masters' if isinstance(graph_assets[key], unreal.Material) else 'Functions')
    clones[key] = result
    for expression in expressions(result):
        if isinstance(expression, unreal.MaterialExpressionMaterialFunctionCall):
            child = expression.get_editor_property('material_function')
            # Existing repaired copies already point to their local child.
            if child and path(child) in graph_assets and affected(path(child)):
                expression.set_editor_property('material_function', clone_graph(path(child)))
        if key in TARGET_FUNCTIONS and eligible(expression):
            expression.set_editor_property('sampler_source', unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
            REPORT['changed_samples'].append({'function': path(result), 'expression': expression.get_name()})
    # A newly duplicated function call can lack transient pin pointers, so its
    # editor-property retarget cannot reliably preserve connections by name.
    # Restore exact original edges after retargeting, using local pin GUIDs.
    wiring_errors = list(unreal.CarnivalMaterialRepairLibrary.restore_material_graph_connections(graph_assets[key], result))
    if wiring_errors:
        raise RuntimeError('Graph connection restoration failed: ' + json.dumps(wiring_errors))
    if isinstance(result, unreal.MaterialFunction):
        ML.update_material_function(result)
    else:
        compiler_errors = list(ML.recompile_material(result))
        if compiler_errors:
            raise RuntimeError('Local master compilation failed: ' + json.dumps(compiler_errors))
    return result


def has_source_master(instance):
    seen = set()
    while isinstance(instance, unreal.MaterialInstanceConstant) and path(instance) not in seen:
        seen.add(path(instance))
        instance = instance.get_editor_property('parent')
    return path(instance) == SOURCE_MASTER


def clone_parent(source):
    key = path(source)
    if key.startswith('/Game/Carnival/Crowd/Collections/') and ':' in key:
        # Generated MICs inherit other MICs embedded in the same collection.
        # Those are repaired in place as part of `instances`; never duplicate a
        # subobject as a top-level asset or flatten its character-specific values.
        return source
    if key == SOURCE_MASTER:
        return clones[SOURCE_MASTER]
    if key in clones:
        return clones[key]
    if not isinstance(source, unreal.MaterialInstanceConstant):
        raise RuntimeError('Unsupported skin parent: ' + str(key))
    result = duplicate(source, 'Instances')
    clones[key] = result
    ML.set_material_instance_parent(result, clone_parent(source.get_editor_property('parent')))
    return result


def repair_pipeline(collection):
    pipeline = collection.get_editor_property('pipeline')
    editor = pipeline.get_editor_property('editor_pipeline')
    try:
        overrides = editor.get_editor_property('FaceMaterialOverrides')
        if not overrides:
            raise RuntimeError('Reflected face_material_overrides is empty; no authored slot mapping to preserve')
        changes = []
        for override in overrides:
            for field in ('ActorMaterial', 'InstancedMaterial'):
                value = override.get_editor_property(field)
                material = value if isinstance(value, unreal.MaterialInterface) else unreal.load_asset(str(value)) if value else None
                if material and (has_source_master(material) or path(material) == SOURCE_MASTER):
                    replacement = clone_parent(material)
                    override.set_editor_property(field, replacement)
                    changes.append({'slot': str(override.get_editor_property('SlotName')),
                                    'field': field, 'old': path(material), 'new': path(replacement)})
        editor.set_editor_property('FaceMaterialOverrides', overrides)
        REPORT['pipeline_overrides'].append({'collection': path(collection), 'changes': changes})
    except Exception as exc:
        # Do not invent slot mappings or change a vendor pipeline to hide this gap.
        REPORT['unresolved_pipeline_overrides'].append({'collection': path(collection), 'error': repr(exc),
            'visible_material_attributes': [name for name in dir(editor) if 'material' in name.lower()]})


try:
    inventory = json.loads((OUT / 'CrowdSamplerGraph.json').read_text())
    collections = [unreal.load_asset(key.split('.')[0]) for key in inventory['collections']]
    if not collections or not all(collections):
        raise RuntimeError('Missing inspected crowd collections')
    prefixes = tuple(path(collection) + ':' for collection in collections)
    instances = [obj for obj in unreal.ObjectIterator(unreal.MaterialInstanceConstant)
                 if path(obj).startswith(prefixes) and has_source_master(obj)]
    if not instances:
        raise RuntimeError('No embedded skin instances still use the affected vendor master')
    inspect_graph(unreal.load_asset(SOURCE_MASTER))
    if not TARGET_FUNCTIONS.issubset(graph_assets):
        raise RuntimeError('Inspected dependency graph differs from the repair plan')
    candidates = [expression for key in TARGET_FUNCTIONS for expression in expressions(graph_assets[key]) if eligible(expression)]
    if len(candidates) != 12:
        raise RuntimeError('Expected exactly 12 verified wrap samples, found ' + str(len(candidates)))
    # Check effective character overrides before changing any parameter sampler.
    for expression in candidates:
        if isinstance(expression, unreal.MaterialExpressionTextureSampleParameter2D):
            name = expression.get_editor_property('parameter_name')
            for instance in instances:
                texture = ML.get_material_instance_texture_parameter_value(instance, name)
                if texture and (texture.get_editor_property('address_x') != unreal.TextureAddress.TA_WRAP
                                or texture.get_editor_property('address_y') != unreal.TextureAddress.TA_WRAP
                                or texture.get_editor_property('filter') != unreal.TextureFilter.TF_DEFAULT
                                or texture.get_editor_property('virtual_texture_streaming')):
                    raise RuntimeError('Incompatible effective texture for ' + str(name) + ': ' + path(texture))
    for collection in collections:
        backup(path(collection))
    clone_graph(SOURCE_MASTER)
    for instance in instances:
        previous = instance.get_editor_property('parent')
        replacement = clone_parent(previous)
        if replacement == previous:
            REPORT['preserved_embedded_parent_links'].append({'path': path(instance), 'parent': path(previous)})
            continue
        ML.set_material_instance_parent(instance, replacement)
        REPORT['reparented_instances'].append({'path': path(instance), 'old': path(previous), 'new': path(replacement)})
    for collection in collections:
        repair_pipeline(collection)
    for asset in list(clones.values()) + collections:
        if not AL.save_loaded_asset(asset, only_if_is_dirty=False):
            raise RuntimeError('Save failed: ' + path(asset))
        REPORT['saved_packages'].append(path(asset))
    REPORT['status'] = 'saved_needs_sm5_cook_and_render_verification'
except Exception:
    REPORT['status'] = 'failed'
    REPORT['errors'].append(traceback.format_exc())
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'CrowdSamplerRepair.json').write_text(json.dumps(REPORT, indent=2))
    unreal.log('CROWD_SAMPLER_REPAIR ' + json.dumps({'status': REPORT['status'], 'samples': len(REPORT['changed_samples']),
                                                 'instances': len(REPORT['reparented_instances']), 'errors': REPORT['errors']}))
    unreal.SystemLibrary.quit_editor()
