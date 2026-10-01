"""Compare playback metadata against the earlier saved G1 candidate; save no assets."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/G1AnimationEventPreservationPublicAPI_20260930';OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'index.json').exists(),'Preserve prior evidence'
REPORT={'success':False,'errors':[],'assets_saved':False,'comparisons':[],
 'limits':'Playback rate, duration, notify and sync-marker counts against original saved G1 Parts clips. Does not establish runtime event delivery or audio acceptance.'}
folders=('G1Parts','G1PartsRetargeted')
builds=[json.loads((ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930'/f/'index.json').read_text()) for f in folders]
files={r['file']:r['sha256'] for b in builds for r in b['new_packages']};files.update(builds[1]['source_hashes_after'])
def hashes():return {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files}
def metadata(clip):
 return {'duration':clip.get_play_length(),'rate_scale':clip.get_editor_property('rate_scale'),
  'notify_count':len(unreal.AnimationLibrary.get_animation_notify_events(clip)),
  'sync_marker_count':len(unreal.AnimationLibrary.get_animation_sync_markers(clip))}
try:
 REPORT['hashes_before']=hashes();assert REPORT['hashes_before']==files
 for animation in ('Idle','Walk'):
  for name in ['AS_'+animation]+['AS_'+head+'_'+animation+'_Baked' for head in ('Dean','MHC_Advika','Kate','Petra')]:
   clips=[unreal.load_object(None,b['collection']+':'+name) for b in builds];assert all(isinstance(c,unreal.AnimSequence) for c in clips),name
   before,after=[metadata(c) for c in clips]
   REPORT['comparisons'].append({'clip':name,'before':before,'after':after,'equal':before==after})
 assert all(r['equal'] for r in REPORT['comparisons']),'Saved animation playback metadata changed'
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:
 REPORT['hashes_after']=hashes()
 if REPORT.get('hashes_before')!=REPORT['hashes_after']:REPORT['errors'].append('A candidate/source file changed')
 REPORT['success']=not REPORT['errors']
 (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
