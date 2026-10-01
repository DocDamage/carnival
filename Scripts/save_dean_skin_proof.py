"""Save reviewed stock bake outputs only, leaving collection/source packages unchanged."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
review=json.loads((ROOT/'Saved/CharacterRepairs/DeanSkinRenderedProof_20260930/index.json').read_text())
assert review['success'] and review['visual_review']['isolated_skin_binding']=='pass'
assert review['engine_exit_code']==0 and not review['errors']
files=[ROOT/'Content/Carnival/Crowd/Collections/DA_CarnivalCrowd_G1_FINAL2.uasset',
       ROOT/'Content/Carnival/MetaHumans/Dean.uasset']
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
exec(compile((ROOT/'Scripts/bake_dean_skin_proof.py').read_text(),str(ROOT/'Scripts/bake_dean_skin_proof.py'),'exec'),globals())
OUT=ROOT/'Saved/CharacterRepairs/DeanSkinSavedProof_20260930'
OUT.mkdir(parents=True,exist_ok=True)
REPORT['success']=False;REPORT['assets_saved']=[];REPORT['source_hashes']=[]
REPORT['limits']='Saved reviewed skin bake textures only. Existing crowd/source packages untouched; integration and populated-world acceptance pending.'
try:
    for g in REPORT['graphs']:
        for row in g['textures']:
            texture=unreal.load_object(None,row['asset'])
            package=row['asset'].split('.')[0]
            file=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset')
            assert not file.exists(),'Expected a new proof texture, not an overwrite: '+str(file)
            assert unreal.EditorAssetLibrary.save_loaded_asset(texture,only_if_is_dirty=False),package
            assert file.exists()
            REPORT['assets_saved'].append({'asset':row['asset'],'file':str(file),
                'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'parameter':row['parameter'],
                'srgb':row['srgb'],'compression':row['compression'],'reference_png':row['png']})
    for p in files:
        after=hashlib.sha256(p.read_bytes()).hexdigest()
        REPORT['source_hashes'].append({'file':str(p),'before':before[str(p)],'after':after})
        assert before[str(p)]==after,'Unexpected source package change: '+str(p)
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
