"""Bind reviewed Dean bake outputs, preserving all loaded mesh/material state outside that edit."""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/DeanCrowdSkinBinding_20260930'
OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'backups':[],'changes':[],'meshes_before':{},'materials_before':{},
        'limits':'Dean face binding only. Mesh digest describes loaded runtime geometry/maps, after Unreal post-load fixes; it does not validate the original invalid clothing-slot design. Full crowd/LOD/presentation acceptance pending.'}
PACKAGE='/Game/Carnival/Crowd/Collections/DA_CarnivalCrowd_G1_FINAL2'
ML=unreal.MaterialEditingLibrary
def path(o): return o.get_path_name() if o else None
def snapshot(m):
    return {'parent':path(m.get_editor_property('parent')),
        'textures':{str(n):path(ML.get_material_instance_texture_parameter_value(m,n)) for n in ML.get_texture_parameter_names(m)},
        'scalars':{str(n):ML.get_material_instance_scalar_parameter_value(m,n) for n in ML.get_scalar_parameter_names(m)},
        'vectors':{str(n):list(ML.get_material_instance_vector_parameter_value(m,n).to_tuple()) for n in ML.get_vector_parameter_names(m)},
        'switches':{str(n):ML.get_material_instance_static_switch_parameter_value(m,n) for n in ML.get_static_switch_parameter_names(m)}}
def loaded_meshes(prefix):
    return {path(m):unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(m)
            for m in unreal.ObjectIterator(unreal.SkeletalMesh) if path(m).startswith(prefix)}
try:
    proof=json.loads((ROOT/'Saved/CharacterRepairs/DeanSkinSavedProof_20260930/index.json').read_text())
    reload=json.loads((ROOT/'Saved/CharacterRepairs/DeanSkinSavedProof_20260930/Reload.json').read_text())
    visual=json.loads((ROOT/'Saved/CharacterRepairs/DeanSkinRenderedProof_20260930/index.json').read_text())
    assert proof['success'] and reload['success'] and visual['success']
    assert visual['visual_review']['isolated_skin_binding']=='pass'
    textures={}
    for row in proof['assets_saved']:
        assert hashlib.sha256(Path(row['file']).read_bytes()).hexdigest()==row['sha256']
        textures[row['parameter']]=unreal.load_asset(row['asset']);assert textures[row['parameter']]
    assert len(textures)==4
    backup=OUT/'Backups'
    for extension in ('.uasset','.uexp','.ubulk'):
        source=ROOT/'Content'/(PACKAGE.removeprefix('/Game/')+extension)
        if not source.exists():continue
        target=backup/source.relative_to(ROOT/'Content')
        assert not target.exists(),'Preserve existing backup; inspect outcome before rerunning'
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        assert hashlib.sha256(target.read_bytes()).hexdigest()==before
        REPORT['backups'].append({'original':str(source),'backup':str(target),'sha256':before})
    c=unreal.load_asset(PACKAGE);assert c
    prefix=c.get_path_name()+':'
    materials={path(m):m for m in unreal.ObjectIterator(unreal.MaterialInstanceConstant) if path(m).startswith(prefix)}
    REPORT['meshes_before']=loaded_meshes(prefix)
    assert REPORT['meshes_before']
    REPORT['materials_before']={p:snapshot(m) for p,m in materials.items()}
    targets={p:m for p,m in materials.items() if m.get_name().startswith(('MI_Face_Dean_','MI_FaceCombo_Dean_'))}
    assert len(targets)==8,len(targets)
    for p,m in targets.items():
        for name,texture in textures.items():
            ML.set_material_instance_texture_parameter_value(m,name,texture)
            assert ML.get_material_instance_texture_parameter_value(m,name)==texture,(p,name)
        ML.set_material_instance_static_switch_parameter_value(m,'Use Baked Material',True)
        assert ML.get_material_instance_static_switch_parameter_value(m,'Use Baked Material'),p
        ML.update_material_instance(m)
        REPORT['changes'].append({'material':p,'textures':{n:path(t) for n,t in textures.items()},'use_baked_material':True})
    for p,m in materials.items():
        expected=json.loads(json.dumps(REPORT['materials_before'][p]))
        if p in targets:
            expected['textures'].update({n:path(t) for n,t in textures.items()})
            expected['switches']['Use Baked Material']=True
        assert snapshot(m)==expected,'Unexpected material parameter/parent change: '+p
    assert loaded_meshes(prefix)==REPORT['meshes_before'],'Loaded mesh geometry/mappings changed before save'
    assert unreal.EditorAssetLibrary.save_loaded_asset(c,only_if_is_dirty=False),PACKAGE
    REPORT['saved_package']=PACKAGE
    REPORT['saved_sha256']=hashlib.sha256(Path(REPORT['backups'][0]['original']).read_bytes()).hexdigest()
    assert loaded_meshes(prefix)==REPORT['meshes_before'],'Loaded mesh structure changed during save'
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
