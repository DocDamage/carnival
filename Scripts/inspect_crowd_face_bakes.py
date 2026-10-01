"""Inventory saved face texture bindings and source pipelines without asset writes."""
import hashlib,json,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/CrowdFaceBakeSurvey_20260930'
OUT.mkdir(parents=True,exist_ok=True)
ML=unreal.MaterialEditingLibrary
REPORT={'success':False,'errors':[],'assets_modified':False,'collections':[], 'face_materials':[],
        'textures':[], 'source_pipelines':[], 'limits':'Read-only saved-object inventory. Baked texture presence and shader-active bindings still require rendered acceptance.'}

def path(obj): return obj.get_path_name() if obj else None
def value(record):
    info=record.get_editor_property('parameter_info')
    return {'name':str(info.get_editor_property('name')),'association':str(info.get_editor_property('association')),
        'index':info.get_editor_property('index'),'value':path(record.get_editor_property('parameter_value'))}

try:
    collections=[]
    for group in range(1,7):
        package=f'/Game/Carnival/Crowd/Collections/DA_CarnivalCrowd_G{group}_FINAL2'
        file=ROOT/'Content'/Path(package.removeprefix('/Game/')).with_suffix('.uasset')
        before=hashlib.sha256(file.read_bytes()).hexdigest()
        asset=unreal.load_asset(package); assert asset
        collections.append(asset)
        REPORT['collections'].append({'package':package,'file':str(file),'sha256_before':before})
    prefixes=tuple(path(c)+':' for c in collections)
    for asset in unreal.ObjectIterator(unreal.MaterialInstanceConstant):
        if not path(asset).startswith(prefixes): continue
        # Include original UI skin MICs retained alongside reparented crowd MICs.
        if not any(t in asset.get_name().lower() for t in ('face','skin')): continue
        row={'path':path(asset),'parent':path(asset.get_editor_property('parent')),
            'texture_overrides':[value(p) for p in asset.get_editor_property('texture_parameter_values')],
            'baked_textures':[], 'static_switches':[]}
        for name in ('Basecolor','Basecolor Baked','Basecolor Baked VT','SRMF Baked','Normal Baked','Normal LOD Baked'):
            tex=ML.get_material_instance_texture_parameter_value(asset,name)
            row['baked_textures'].append({'name':name,'texture':path(tex)})
        row['static_switches']=[{'name':str(name),'value':ML.get_material_instance_static_switch_parameter_value(asset,name)}
            for name in ML.get_static_switch_parameter_names(asset)]
        REPORT['face_materials'].append(row)
    for texture in unreal.ObjectIterator(unreal.Texture2D):
        if not path(texture).startswith(prefixes): continue
        REPORT['textures'].append({'path':path(texture),'name':texture.get_name()})
    for pipeline in unreal.ObjectIterator(unreal.Object):
        # Function-library CDOs can shadow UObject.get_class with static methods.
        cls=unreal.Object.get_class(pipeline)
        if not cls or cls.get_name() != 'MetaHumanCrowdCharacterEditorPipeline': continue
        REPORT['source_pipelines'].append({'path':path(pipeline),
            'face_mesh':path(pipeline.get_editor_property('FaceMesh')),
            'body_mesh':path(pipeline.get_editor_property('BodyMesh'))})
    for row in REPORT['collections']:
        row['sha256_after']=hashlib.sha256(Path(row['file']).read_bytes()).hexdigest()
        assert row['sha256_before']==row['sha256_after']
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc()); raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
