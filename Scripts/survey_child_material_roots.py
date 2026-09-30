"""Read saved material output wiring and texture bindings behind child slots."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
REPORT={'success':False,'materials':[],'errors':[],
    'limits':'Read-only saved graph/binding census. Rendered grey appearance remains unaccepted until diagnosed and repaired.'}
source=json.loads((OUT/'Child_Guest_Blueprints.json').read_text());assert source['success']
mel=unreal.MaterialEditingLibrary;seen=set()
try:
    for child in source['children']:
        mesh=unreal.load_asset(child['mesh'])
        for slot in mesh.materials:
            instance=slot.material_interface;assert instance
            path=instance.get_path_name()
            if path in seen:continue
            seen.add(path);chain=[path];root=instance
            while isinstance(root,unreal.MaterialInstance):
                root=root.get_editor_property('parent');assert root
                chain.append(root.get_path_name());assert len(chain)<20
            assert isinstance(root,unreal.Material)
            properties={}
            for name in ('BASE_COLOR','MATERIAL_ATTRIBUTES','NORMAL','ROUGHNESS','OPACITY','OPACITY_MASK'):
                enum=getattr(unreal.MaterialProperty,'MP_'+name,None)
                if enum is None:continue
                node=mel.get_material_property_input_node(root,enum)
                properties[name]={'node':node.get_path_name() if node else None,
                    'output':mel.get_material_property_input_node_output_name(root,enum) if node else None}
            textures=[]
            for name in mel.get_texture_parameter_names(instance):
                texture=mel.get_material_instance_texture_parameter_value(instance,name) if isinstance(instance,unreal.MaterialInstance) else mel.get_material_default_texture_parameter_value(root,name)
                textures.append({'parameter':str(name),'texture':texture.get_path_name() if texture else None})
            vectors=[]
            for name in mel.get_vector_parameter_names(instance):
                value=mel.get_material_instance_vector_parameter_value(instance,name) if isinstance(instance,unreal.MaterialInstance) else mel.get_material_default_vector_parameter_value(root,name)
                vectors.append({'parameter':str(name),'linear_rgba':[value.r,value.g,value.b,value.a]})
            scalars=[]
            for name in mel.get_scalar_parameter_names(instance):
                value=mel.get_material_instance_scalar_parameter_value(instance,name) if isinstance(instance,unreal.MaterialInstanceConstant) else mel.get_material_default_scalar_parameter_value(root,name)
                scalars.append({'parameter':str(name),'value':value})
            switches=[]
            for name in mel.get_static_switch_parameter_names(instance):
                value=mel.get_material_instance_static_switch_parameter_value(instance,name) if isinstance(instance,unreal.MaterialInstanceConstant) else mel.get_material_default_static_switch_parameter_value(root,name)
                switches.append({'parameter':str(name),'value':value})
            REPORT['materials'].append({'identity':child['identity'],'slot':str(slot.material_slot_name),
                'parent_chain':chain,'output_nodes':properties,'texture_parameters':textures,
                'vector_parameters':vectors,
                'scalar_parameters':scalars,'static_switch_parameters':switches,
                'blend_mode':str(root.get_editor_property('blend_mode')),
                'two_sided':root.get_editor_property('two_sided'),
                'uses_material_attributes':root.get_editor_property('use_material_attributes')})
    REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc())
(OUT/'Child_Material_Roots.json').write_text(json.dumps(REPORT,indent=2))
