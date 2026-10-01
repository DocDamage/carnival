"""Generate temporary Dean face and inspect stock skin bake templates; no saves."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/GeneratedSourceFaceSurvey_20260930'
OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'assets_saved':False,'materials':[],'bake_graphs':[]}
def path(o): return o.get_path_name() if o else None
try:
    character=unreal.load_asset('/Game/Carnival/MetaHumans/Dean')
    face,error=unreal.CarnivalCrowdMaterialEditorLibrary.generate_source_face(character)
    assert face and not error,error
    REPORT['source_face']=path(face)
    ml=unreal.MaterialEditingLibrary
    for slot in face.get_editor_property('materials'):
        mat=slot.get_editor_property('material_interface')
        REPORT['materials'].append({'slot':str(slot.get_editor_property('material_slot_name')),
            'material':path(mat),'parent':path(mat.get_editor_property('parent')) if isinstance(mat,unreal.MaterialInstance) else None,
            'textures':[{'name':str(n),'path':path(mat.get_texture_parameter_value(n) if isinstance(mat,unreal.MaterialInstanceDynamic)
                else ml.get_material_instance_texture_parameter_value(mat,n) if isinstance(mat,unreal.MaterialInstanceConstant)
                else ml.get_material_default_texture_parameter_value(mat,n))}
                for n in ml.get_texture_parameter_names(mat)]})
    settings=unreal.load_asset('/MetaHumanCharacter/TextureGraphs/FaceDefaultMaterialBakingSettings_sRGB')
    for graph in settings.get_editor_property('TextureGraphs'):
        REPORT['bake_graphs'].append({'template':path(graph.get_editor_property('TextureGraphInstance')),
            'input_values':{str(k):v for k,v in graph.get_editor_property('InputValues').items()},
            'input_materials':[{'slot':str(i.get_editor_property('SourceMaterialSlotName')),
                'input_name':str(i.get_editor_property('InputParameterName')),
                'lod':i.get_editor_property('MainSectionTopLODIndex')} for i in graph.get_editor_property('InputMaterials')],
            'outputs':[{'graph_name':str(o.get_editor_property('OutputTextureNameInGraph')),
                'name':str(o.get_editor_property('OutputTextureName')),
                'parameter':str(o.get_editor_property('OutputMaterialParameterName')),
                'slots':[str(s) for s in o.get_editor_property('OutputMaterialSlotNames')]}
                for o in graph.get_editor_property('OutputTextures')]})
    assert REPORT['materials'] and REPORT['bake_graphs']
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc()); raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
