import json
from pathlib import Path
import unreal
r = {'key_doc': unreal.Key.__doc__, 'import_doc': unreal.Key.import_text.__doc__, 'keys': []}
for raw in ['F', '(KeyName="F")']:
    k = unreal.Key()
    try:
        v = k.import_text(raw)
        r['keys'].append({'raw':raw, 'original':k.export_text(), 'value':str(v), 'value_type':str(type(v)), 'export':v.export_text() if isinstance(v,unreal.Key) else None})
    except Exception as e:r['keys'].append({'raw':raw,'error':str(e)})
context = unreal.load_asset('/Game/Carnival/Input/IMC_CarnivalPlayer')
r['mappings'] = [{'action':m.action.get_name(), 'key':m.key.export_text(), 'modifiers':[o.get_class().get_name() for o in m.modifiers]} for m in context.get_editor_property('default_key_mappings').mappings]
r['skeleton_api'] = [n for n in dir(unreal.Skeleton) if any(k in n for k in ['compat','bone','pose'])]
for p in ['/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple','/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple']:
    m=unreal.load_asset(p)
    r[p]=m.get_editor_property('skeleton').get_path_name()
Path(r'F:\Carnival\Saved\RideDevelopment\Authoring_Probe.json').write_text(json.dumps(r,indent=2))
