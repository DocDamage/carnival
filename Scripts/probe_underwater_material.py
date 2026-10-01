import json,unreal
m=unreal.load_asset('/Game/Carnival/World/Materials/Water/M_CarnivalUnderwaterPP')
R={'domain':str(m.get_editor_property('material_domain')),'blendable':str(m.get_editor_property('blendable_location'))}
try:
 st=unreal.MaterialEditingLibrary.get_statistics(m);R['stats']={k:str(getattr(st,k)) for k in dir(st) if not k.startswith('_') and not callable(getattr(st,k))}
except Exception as e:R['stats_err']=str(e)
R['expressions']=[e.get_class().get_name() for e in unreal.MaterialEditingLibrary.get_material_expressions(m)] if hasattr(unreal.MaterialEditingLibrary,'get_material_expressions') else 'n/a'
R['emissive_node']=str(unreal.MaterialEditingLibrary.get_material_property_input_node(m,unreal.MaterialProperty.MP_EMISSIVE_COLOR))
open(r'F:\Carnival\Saved\CharacterRepairs\UnderwaterMaterialProbe_20261001.json','w').write(json.dumps(R,indent=1,default=str))
