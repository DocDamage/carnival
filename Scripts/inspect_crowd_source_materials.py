"""Inspect source MetaHuman assets and editable skin inputs without saving."""
import json,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/CrowdSourceMaterialSurvey_20260930'
OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'items':[],'materials':[],'pipelines':[],'assets_saved':False}
def path(o): return o.get_path_name() if o else None
try:
    c=unreal.load_asset('/Game/Carnival/Crowd/Collections/DA_CarnivalCrowd_G1_FINAL2')
    prefix=c.get_path_name()+':'
    for w in list(unreal.ObjectIterator(unreal.Object)):
        cls=unreal.Object.get_class(w)
        if not cls or cls.get_name()!='MetaHumanWardrobeItem' or not path(w).startswith(prefix): continue
        ref=w.get_editor_property('PrincipalAsset')
        soft=ref.get_editor_property('Asset')
        source=soft if isinstance(soft,unreal.Object) else unreal.load_asset(str(soft))
        if not source or unreal.Object.get_class(source).get_name()!='MetaHumanCharacter': continue
        pipeline=w.get_editor_property('Pipeline')
        row={'wardrobe':path(w),'source':path(source),'class':unreal.Object.get_class(source).get_name()}
        for prop in ('SynthesizedFaceTexturesInfo','SynthesizedFaceTextures','BodyTextures','bHasHighResolutionTextures'):
            row[prop]=str(source.get_editor_property(prop))
        REPORT['items'].append(row)
        if not pipeline: continue
        pipeline=pipeline.get_editor_property('EditorPipeline')
        REPORT['pipelines'].append({'path':path(pipeline),'class':unreal.Object.get_class(pipeline).get_name(),
            'face_mesh':path(pipeline.get_editor_property('FaceMesh')),
            'body_mesh':path(pipeline.get_editor_property('BodyMesh'))})
    ml=unreal.MaterialEditingLibrary
    for m in unreal.ObjectIterator(unreal.MaterialInstanceConstant):
        if not any(t in m.get_name().lower() for t in ('face','skin')): continue
        if path(m).startswith('/Engine') or path(m).startswith('/MetaHuman'): continue
        REPORT['materials'].append({'path':path(m),'parent':path(m.get_editor_property('parent')),
            'textures':[{'name':str(n),'value':path(ml.get_material_instance_texture_parameter_value(m,n))}
                for n in ml.get_texture_parameter_names(m)]})
    assert REPORT['items'], 'No source MetaHuman characters inspected'
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc()); raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
