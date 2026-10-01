"""One backed-up collection per process; scoped edits require reviewed head candidates."""
import hashlib,json,os,re,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
GROUP=os.environ['CARNIVAL_BIND_GROUP'];assert GROUP in ['G'+str(i) for i in range(1,7)]
PACKAGE='/Game/Carnival/Crowd/Collections/DA_CarnivalCrowd_'+GROUP+'_FINAL2'
OUT=ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBindings_20260930'/GROUP
OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'backups':[],'changes':[],'meshes_before':{},'materials_before':{},
    'limits':'Head skin textures/switches only. Mesh fingerprints cover runtime-normalized loaded structure, not original invalid clothing-slot intent or full asset metadata. GPU/all LOD/full-body/population review remains required.'}
ROSTER={'G1':['Dean','Kate','MHC_Advika','Petra'],'G2':['MHC_Hannah','MHC_Kabir','Mason'],
        'G3':['MHC_Crowd84','MHC_Seo','Skye'],'G4':['AmandaBlack','MHC_Natasha'],
        'G5':['Kate','MHC_Natasha','Skotukeda3','Skotukeda4'],'G6':['MHC_Base_Female']}[GROUP]
ML=unreal.MaterialEditingLibrary
def path(o):return o.get_path_name() if o else None
def snapshot(m):
    return {'parent':path(m.get_editor_property('parent')),
        'textures':{str(n):path(ML.get_material_instance_texture_parameter_value(m,n)) for n in ML.get_texture_parameter_names(m)},
        'scalars':{str(n):ML.get_material_instance_scalar_parameter_value(m,n) for n in ML.get_scalar_parameter_names(m)},
        'vectors':{str(n):list(ML.get_material_instance_vector_parameter_value(m,n).to_tuple()) for n in ML.get_vector_parameter_names(m)},
        'switches':{str(n):ML.get_material_instance_static_switch_parameter_value(m,n) for n in ML.get_static_switch_parameter_names(m)}}
def meshes(prefix):
    return {path(m):unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(m)
        for m in unreal.ObjectIterator(unreal.SkeletalMesh) if path(m).startswith(prefix)}
def save():(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
try:
    visual=json.loads((ROOT/'Saved/CharacterRepairs/CrowdHeadSkinCandidatesAcceptance_20260930/index.json').read_text())
    assert visual['success'] and visual['capture_success'] and not visual['errors']
    textures={}
    for name in ROSTER:
        if name=='Dean':
            proofdir=ROOT/'Saved/CharacterRepairs/DeanSkinSavedProof_20260930'
            proof=json.loads((proofdir/'index.json').read_text());rows=proof['assets_saved']
            prior=json.loads((ROOT/'Saved/CharacterRepairs/DeanSkinRenderedProof_20260930/index.json').read_text())
            assert prior['visual_review']['isolated_skin_binding']=='pass' and prior['success']
        else:
            assert visual['visual_review']['heads'][name]['isolated_skin_binding']=='pass',name
            proofdir=ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBakes_20260930'/name
            proof=json.loads((proofdir/'index.json').read_text());rows=proof['saved_textures']
        reload=json.loads((proofdir/'Reload.json').read_text())
        assert proof['success'] and reload['success'] and not proof['errors'] and not reload['errors']
        textures[name]={}
        for row in rows:
            assert hashlib.sha256(Path(row['file']).read_bytes()).hexdigest()==row['sha256']
            texture=unreal.load_asset(row['asset']);assert texture,row['asset']
            textures[name][row['parameter']]=texture
        assert len(textures[name])==4
    for extension in ('.uasset','.uexp','.ubulk'):
        source=ROOT/'Content'/(PACKAGE.removeprefix('/Game/')+extension)
        if not source.exists():continue
        target=OUT/'Backups'/source.relative_to(ROOT/'Content')
        assert not target.exists(),'Preserve previous backup and inspect outcome before rerunning'
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        digest=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
        REPORT['backups'].append({'original':str(source),'backup':str(target),'sha256':digest});save()
    collection=unreal.load_asset(PACKAGE);assert collection
    prefix=collection.get_path_name()+':'
    materials={path(m):m for m in unreal.ObjectIterator(unreal.MaterialInstanceConstant) if path(m).startswith(prefix)}
    REPORT['materials_before']={p:snapshot(m) for p,m in materials.items()}
    REPORT['meshes_before']=meshes(prefix);assert REPORT['meshes_before']
    targets={}
    counts={name:0 for name in ROSTER}
    for p,m in materials.items():
        match=re.fullmatch(r'MI_Face(?:Combo)?_(.+)_head_LOD.+',m.get_name())
        if not match:continue
        name=match[1];assert name in ROSTER,name
        targets[p]=name;counts[name]+=1
    assert counts=={name:(4 if GROUP=='G6' else 8) for name in ROSTER},counts
    REPORT['target_counts']=counts;save()
    for p,name in targets.items():
        m=materials[p]
        for parameter,texture in textures[name].items():
            ML.set_material_instance_texture_parameter_value(m,parameter,texture)
            assert ML.get_material_instance_texture_parameter_value(m,parameter)==texture,(p,parameter)
        ML.set_material_instance_static_switch_parameter_value(m,'Use Baked Material',True)
        assert ML.get_material_instance_static_switch_parameter_value(m,'Use Baked Material')
        ML.update_material_instance(m)
        REPORT['changes'].append({'material':p,'head':name,'textures':{n:path(t) for n,t in textures[name].items()},'use_baked_material':True})
    for p,m in materials.items():
        expected=json.loads(json.dumps(REPORT['materials_before'][p]))
        if p in targets:
            expected['textures'].update({n:path(t) for n,t in textures[targets[p]].items()})
            expected['switches']['Use Baked Material']=True
        assert snapshot(m)==expected,'Unexpected material state: '+p
    assert meshes(prefix)==REPORT['meshes_before'],'Loaded mesh structure changed before save'
    assert unreal.EditorAssetLibrary.save_loaded_asset(collection,only_if_is_dirty=False),PACKAGE
    REPORT['saved_package']=PACKAGE
    REPORT['saved_sha256']=hashlib.sha256(Path(REPORT['backups'][0]['original']).read_bytes()).hexdigest()
    assert meshes(prefix)==REPORT['meshes_before'],'Loaded mesh structure changed during save'
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:save()
