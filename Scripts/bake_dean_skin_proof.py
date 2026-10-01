"""Bake only Dean's head with stock MetaHuman graphs; export proof PNGs, no asset saves."""
import json,traceback,time
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/DeanSkinBakeProof_20260930'
OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'assets_saved':False,'graphs':[],'visual_review':'pending',
        'limits':'Isolated source-face skin bake only. No crowd assets modified or full character/render acceptance.'}
def path(o): return o.get_path_name() if o else None
try:
    face,error=unreal.CarnivalCrowdMaterialEditorLibrary.generate_source_face(unreal.load_asset('/Game/Carnival/MetaHumans/Dean'))
    assert face and not error,error
    slots={str(s.material_slot_name):s.material_interface for s in face.materials}
    settings=unreal.load_asset('/MetaHumanCharacter/TextureGraphs/FaceDefaultMaterialBakingSettings_sRGB')
    for index,g in enumerate(settings.get_editor_property('TextureGraphs')):
        inputs=g.get_editor_property('InputMaterials')
        if not inputs or any(str(i.get_editor_property('SourceMaterialSlotName'))!='head_shader_shader' for i in inputs): continue
        template=g.get_editor_property('TextureGraphInstance')
        outputs=g.get_editor_property('OutputTextures')
        names={o.get_editor_property('OutputTextureNameInGraph'):o.get_editor_property('OutputTextureName') for o in outputs}
        row={'template':path(template),'input_materials':{},'textures':[],'seconds':None}
        REPORT['graphs'].append(row)
        materials={i.get_editor_property('InputParameterName'):slots[str(i.get_editor_property('SourceMaterialSlotName'))] for i in inputs}
        row['input_materials']={str(k):path(v) for k,v in materials.items()}
        started=time.monotonic()
        textures,error=unreal.CarnivalCrowdMaterialEditorLibrary.bake_proof_material_graph(template,materials,
            g.get_editor_property('InputValues'),names,
            '/Game/Carnival/Crowd/Materials/FaceBakeProof/Dean/Graph'+str(index),512)
        assert textures and not error,error
        row['seconds']=time.monotonic()-started
        for texture in textures:
            image=OUT/(texture.get_name()+'.png')
            task=unreal.AssetExportTask()
            task.object=texture;task.filename=str(image);task.automated=True;task.prompt=False
            task.replace_identical=True;task.exporter=unreal.TextureExporterPNG()
            assert unreal.Exporter.run_asset_export_task(task),path(texture)
            assert image.exists() and image.stat().st_size>100,image
            row['textures'].append({'asset':path(texture),'png':str(image),'srgb':texture.get_editor_property('srgb'),
                'compression':str(texture.get_editor_property('compression_settings')),
                'parameter':str(next(o.get_editor_property('OutputMaterialParameterName') for o in outputs
                    if str(o.get_editor_property('OutputTextureName'))==texture.get_name()))})
        (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
    assert len(REPORT['graphs'])==2,REPORT['graphs']
    assert sum(len(g['textures']) for g in REPORT['graphs'])==4
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc()); raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
