"""Bake one original crowd head per process to bound character-editor memory; no collection writes."""
import hashlib,json,os,re,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
NAME=os.environ['CARNIVAL_HEAD_NAME']
assert re.fullmatch(r'[A-Za-z0-9_]+',NAME),NAME
SOURCES={
 'Dean':'Dean','Kate':'Additional/Kate/Kate','MHC_Advika':'MHC_Advika','Petra':'Additional/Petra/Petra',
 'MHC_Hannah':'MHC_Hannah','MHC_Kabir':'MHC_Kabir','Mason':'Mason',
 'MHC_Crowd84':'Additional/Crowd84/MHC_Crowd84','MHC_Seo':'MHC_Seo','Skye':'Skye',
 'AmandaBlack':'Additional/Amanda/AmandaBlack','MHC_Natasha':'Additional/Natasha/MHC_Natasha',
 'Skotukeda3':'Additional/Skotukeda3/Skotukeda3','Skotukeda4':'Additional/Skotukeda4/Skotukeda4',
 'MHC_Base_Female':'Additional/BaseFemale/MHC_Base_Female'}
assert NAME in SOURCES,NAME
OUT=ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBakes_20260930'/NAME
OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'head':NAME,'graphs':[],'saved_textures':[],
    'source':'/Game/Carnival/MetaHumans/'+SOURCES[NAME],
    'limits':'Stock face skin bake at 512 pixels. Fresh reload, visual identity/skin match, live actor/instanced and all LOD acceptance still required. No crowd collection is written.'}
def save():(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def path(o):return o.get_path_name() if o else None
try:
    sourcefile=ROOT/'Content'/(REPORT['source'].removeprefix('/Game/')+'.uasset')
    REPORT['source_sha256_before']=hashlib.sha256(sourcefile.read_bytes()).hexdigest()
    folder='/Game/Carnival/Crowd/Materials/FaceBakeProof/'+NAME
    assert not (ROOT/'Content'/folder.removeprefix('/Game/')).exists(),'Inspect existing outcome before re-baking '+NAME
    character=unreal.load_asset(REPORT['source']);assert isinstance(character,unreal.MetaHumanCharacter)
    face,error=unreal.CarnivalCrowdMaterialEditorLibrary.generate_source_face(character)
    assert face and not error,error
    slots={str(s.material_slot_name):s.material_interface for s in face.materials}
    settings=unreal.load_asset('/MetaHumanCharacter/TextureGraphs/FaceDefaultMaterialBakingSettings_sRGB')
    alltextures=[]
    for index,g in enumerate(settings.get_editor_property('TextureGraphs')):
        inputs=g.get_editor_property('InputMaterials')
        if not inputs or any(str(i.get_editor_property('SourceMaterialSlotName'))!='head_shader_shader' for i in inputs):continue
        outputs=g.get_editor_property('OutputTextures')
        names={o.get_editor_property('OutputTextureNameInGraph'):o.get_editor_property('OutputTextureName') for o in outputs}
        materials={i.get_editor_property('InputParameterName'):slots[str(i.get_editor_property('SourceMaterialSlotName'))] for i in inputs}
        template=g.get_editor_property('TextureGraphInstance')
        row={'template':path(template),'textures':[]};REPORT['graphs'].append(row);save()
        textures,error=unreal.CarnivalCrowdMaterialEditorLibrary.bake_proof_material_graph(template,materials,
            g.get_editor_property('InputValues'),names,folder+'/Graph'+str(index),512)
        assert textures and not error,error
        for texture in textures:
            image=OUT/(texture.get_name()+'.png')
            task=unreal.AssetExportTask();task.object=texture;task.filename=str(image)
            task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.TextureExporterPNG()
            assert unreal.Exporter.run_asset_export_task(task)
            assert image.exists() and image.stat().st_size>100,image
            param=str(next(o.get_editor_property('OutputMaterialParameterName') for o in outputs
                if str(o.get_editor_property('OutputTextureName'))==texture.get_name()))
            data={'asset':path(texture),'parameter':param,'png':str(image),
                'srgb':texture.get_editor_property('srgb'),'compression':str(texture.get_editor_property('compression_settings'))}
            row['textures'].append(data);alltextures.append((texture,data))
        save()
    assert len(REPORT['graphs'])==2 and len(alltextures)==4
    for texture,data in alltextures:
        assert unreal.EditorAssetLibrary.save_loaded_asset(texture,only_if_is_dirty=False),path(texture)
        file=ROOT/'Content'/(path(texture).split('.')[0].removeprefix('/Game/')+'.uasset')
        REPORT['saved_textures'].append({**data,'file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
        save()
    REPORT['source_sha256_after']=hashlib.sha256(sourcefile.read_bytes()).hexdigest()
    assert REPORT['source_sha256_before']==REPORT['source_sha256_after'],'Original character was modified on disk'
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:save()
