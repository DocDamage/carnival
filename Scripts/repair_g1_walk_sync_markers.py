"""Restore diagnosed candidate-only marker metadata with a package backup and strict source checks."""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/G1WalkSyncMarkerRepair_20260930';OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'index.json').exists(),'Preserve prior repair evidence'
BUILD_FILE=ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930/G1PartsRetargeted/index.json'
build=json.loads(BUILD_FILE.read_text());assert build['success'] and not build['errors']
old=json.loads((BUILD_FILE.parent.parent/'G1Parts/index.json').read_text())
collection_row=next(r for r in build['new_packages'] if r['asset']==build['collection'])
target_file=Path(collection_row['file'])
REPORT={'success':False,'errors':[],'repair':'Restore six original shared-walk sync markers; bone tracks unchanged','assets_saved':[],
 'limits':'Candidate-only metadata correction; fresh reload must repeat pose and metadata checks. Live config unchanged.'}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def markers(clip):return [{'name':str(m.marker_name),'time':m.time} for m in unreal.AnimationLibrary.get_animation_sync_markers(clip)]
def meshstates(prefix):return {m.get_path_name():unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(m)
 for m in unreal.ObjectIterator(unreal.SkeletalMesh) if m.get_path_name().startswith(prefix)}
files=dict(build['source_hashes_after']);files.update({r['file']:r['sha256'] for r in old['new_packages']})
files.update({r['file']:r['sha256'] for r in build['new_packages'] if r is not collection_row})
try:
 assert all(digest(p)==h for p,h in files.items());assert digest(target_file)==collection_row['sha256']
 backup=OUT/'BeforeMarkers.uasset';assert not backup.exists();shutil.copy2(target_file,backup)
 REPORT['backup']={'file':str(backup),'sha256':digest(backup)};assert REPORT['backup']['sha256']==collection_row['sha256']
 (OUT/'BeforeBuildRecord.json').write_text(BUILD_FILE.read_text())
 source=unreal.load_object(None,old['collection']+':AS_Walk')
 collection=unreal.load_asset(build['collection']);assert source and collection
 prefix=collection.get_path_name()+':';REPORT['mesh_states_before']=meshstates(prefix)
 REPORT['expected_markers']=markers(source);REPORT['clips']=[]
 for name in ('AS_Walk','AS_Input_Walk'):
  candidate=unreal.load_object(None,build['collection']+':'+name);assert candidate,name
  row={'clip':name,'markers_before':markers(candidate)};REPORT['clips'].append(row)
  count,error=unreal.CarnivalCrowdMaterialEditorLibrary.restore_candidate_walk_sync_markers(source,candidate);assert count==6 and not error,error
  row['markers_after']=markers(candidate);assert row['markers_after']==REPORT['expected_markers']
 REPORT['mesh_states_after']=meshstates(prefix);assert REPORT['mesh_states_after']==REPORT['mesh_states_before']
 assert unreal.EditorAssetLibrary.save_loaded_asset(collection,only_if_is_dirty=False)
 REPORT['assets_saved'].append(str(target_file));REPORT['package_sha256_after']=digest(target_file)
 REPORT['unchanged_hashes_after']={p:digest(p) for p in files};assert REPORT['unchanged_hashes_after']==files
 build.setdefault('amendments',[]).append({'reason':REPORT['repair'],'before_sha256':collection_row['sha256'],
  'after_sha256':REPORT['package_sha256_after'],'backup':REPORT['backup'],'report':str(OUT/'index.json')})
 collection_row['sha256']=REPORT['package_sha256_after'];BUILD_FILE.write_text(json.dumps(build,indent=2))
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
