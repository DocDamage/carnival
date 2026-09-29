"""Read-only material/function/sampler inventory; does not save or modify assets."""
import json
import re
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
DESTINATION = ROOT / 'Saved/CharacterRepairs/CrowdSamplerGraph.json'
MATERIALS = [
    '/MetaHumanCrowd/Materials/M_skin_unified_baked_crowd',
    '/MetaHumanCharacter/Lookdev_UHM/Skin/Materials/M_skin_unified_UI',
]
REPORT = {'mutated_assets': False, 'graphs': {}, 'instances': [], 'collections': {}, 'errors': []}


def prop(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return None


def texture_info(texture):
    if not texture:
        return None
    return {'path': texture.get_path_name(), 'filter': str(prop(texture, 'filter')),
            'address_x': str(prop(texture, 'address_x')), 'address_y': str(prop(texture, 'address_y')),
            'virtual_texture_streaming': prop(texture, 'virtual_texture_streaming')}


def collection_info(collection):
    if not collection or collection.get_path_name() in REPORT['collections']:
        return
    pipeline = prop(collection, 'pipeline')
    editor = prop(pipeline, 'editor_pipeline')
    overrides = []
    try:
        raw_overrides = editor.get_editor_property('FaceMaterialOverrides') if editor else []
        override_error = None
    except Exception as exc:
        raw_overrides = []
        override_error = repr(exc)
    for override in raw_overrides:
        overrides.append({
            'slot_name': str(prop(override, 'SlotName')),
            'actor_material': str(prop(override, 'ActorMaterial')),
            'instanced_material': str(prop(override, 'InstancedMaterial')),
            'instance_parameter_name_to_custom_data_format': str(prop(override, 'InstanceParameterNameToCustomDataFormat'))})
    REPORT['collections'][collection.get_path_name()] = {
        'pipeline': pipeline.get_path_name() if pipeline else None,
        'pipeline_class': pipeline.get_class().get_name() if pipeline else None,
        'editor_pipeline': editor.get_path_name() if editor else None,
        'editor_pipeline_class': editor.get_class().get_name() if editor else None,
        'face_material_overrides': overrides,
        'face_material_overrides_read_error': override_error}


def graph(asset):
    if not asset or asset.get_path_name() in REPORT['graphs']:
        return
    key = asset.get_path_name()
    row = {'class': asset.get_class().get_name(), 'texture_samples': [], 'functions': [], 'expression_count': 0}
    REPORT['graphs'][key] = row
    if isinstance(asset, unreal.Material):
        expressions = unreal.MaterialEditingLibrary.get_material_expressions(asset)
    elif isinstance(asset, unreal.MaterialFunction):
        expressions = unreal.MaterialEditingLibrary.get_material_function_expressions(asset)
    else:
        parent = prop(asset, 'parent')
        row['parent'] = parent.get_path_name() if parent else None
        graph(parent)
        return
    row['expression_count'] = len(expressions)
    for expression in expressions:
        if isinstance(expression, unreal.MaterialExpressionTextureSample):
            row['texture_samples'].append({
                'name': expression.get_name(), 'class': expression.get_class().get_name(),
                'parameter': str(prop(expression, 'parameter_name')),
                'sampler_source': str(prop(expression, 'sampler_source')),
                'sampler_type': str(prop(expression, 'sampler_type')),
                'mip_value_mode': str(prop(expression, 'mip_value_mode')),
                'texture': texture_info(prop(expression, 'texture'))})
        if isinstance(expression, unreal.MaterialExpressionMaterialFunctionCall):
            function = prop(expression, 'material_function')
            row['functions'].append(function.get_path_name() if function else None)
            graph(function)


for path in MATERIALS:
    try:
        asset = unreal.load_asset(path)
        if not asset:
            raise RuntimeError('Material not found: ' + path)
        graph(asset)
    except Exception as exc:
        REPORT['errors'].append({'asset': path, 'error': repr(exc)})

warning_report = ROOT / 'Saved/WorldExpansion/Runtime_Warning_Review.json'
if warning_report.exists():
    failures = json.loads(warning_report.read_text()).get('material_compile_failures', [])
    paths = sorted(set(path for failure in failures for path in re.findall(r'\(MI:([^\)]+)\)', failure)
                       if path.startswith('/Game/Carnival/Crowd/Collections/')))
    for path in paths:
        try:
            # Loading the outer package constructs its embedded material exports.
            collection_info(unreal.load_asset(path.split('.')[0]))
            instance = unreal.load_object(None, path)
            if not instance:
                raise RuntimeError('Embedded material not found')
            parents = []
            parent = prop(instance, 'parent')
            while parent and parent.get_path_name() not in parents:
                parents.append(parent.get_path_name())
                if isinstance(parent, unreal.Material):
                    graph(parent)
                    break
                parent = prop(parent, 'parent')
            textures = []
            for value in prop(instance, 'texture_parameter_values') or []:
                parameter = prop(value, 'parameter_info')
                textures.append({'parameter': str(prop(parameter, 'name')),
                                 'value': texture_info(prop(value, 'parameter_value'))})
            REPORT['instances'].append({'path': path, 'parent_chain': parents, 'texture_overrides': textures})
        except Exception as exc:
            REPORT['errors'].append({'asset': path, 'error': repr(exc)})

DESTINATION.parent.mkdir(parents=True, exist_ok=True)
DESTINATION.write_text(json.dumps(REPORT, indent=2, default=str))
unreal.log('CROWD_SAMPLER_GRAPH ' + json.dumps({'report': str(DESTINATION), 'graphs': len(REPORT['graphs']),
                                            'instances': len(REPORT['instances']), 'errors': REPORT['errors']}))
unreal.SystemLibrary.quit_editor()
