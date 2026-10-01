"""Refresh verified evidence, retaining earlier snapshots and acceptance limits."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(r'F:\Carnival')
BASE=ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930'
campaign=ROOT/'Saved/CampaignAcceptance/SignalNetwork_20260930'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path,data):path.write_text(json.dumps(data,indent=2))
tests=read(campaign/'NativeRegression.json')
assert tests['succeeded']==40 and not any(tests.get(k,0) for k in ('failed','notRun','inProcess','succeededWithWarnings'))
for name in ('EditorBuildAfterReplayUnlock.log','GameBuildAfterReplayUnlock.log'):
 text=(campaign/name).read_text(errors='replace');assert 'Result: Succeeded' in text,name
record=read(campaign/'index.json')
backup=campaign/'BeforeVerifiedReplayUnlock.json';assert not backup.exists();shutil.copy2(campaign/'index.json',backup)
files=[Path(p) for p in record['source_sha256']]
files.append(ROOT/'Source/CarnivalGame/CarnivalMissionSubsystem.cpp')
record['source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
record.pop('pending_replay_unlock_regression',None);record.pop('validation_limit',None)
record['rescue_unlock_survives_replay_before_first_sequel_station']=True
record['native_tests']={k:tests.get(k,0) for k in ('succeeded','succeededWithWarnings','failed','notRun','inProcess')}
record['verified_build_logs']=[str(campaign/n) for n in ('EditorBuildAfterReplayUnlock.log','GameBuildAfterReplayUnlock.log')]
record['world_survey_report']=str(ROOT/'Saved/CampaignAcceptance/ConnectedWorldSites_20260930/index.json')
write(campaign/'index.json',record)
folder=BASE/'G2PartsRetargetedLOD0';build=read(folder/'index.json');reload=read(folder/'Reload.json')
assert build['success'] and reload['success'] and not build['errors'] and not reload['errors']
gallery=[]
for pose in ('Idle','Walk'):
 path=ROOT/f'Saved/CharacterRepairs/G2PartsLOD0SavedActor{pose}_20260930/index.json'
 r=read(path);assert r['capture_success'] and not r['errors'] and len(r['captures'])==12 and r['engine_exit_code']==0
 gallery.append(str(path))
review={'success':False,'assets_saved':False,'capture_reports':gallery,'inspected_captures':24,
 'inspection':'All six front/back Idle and Walk views reviewed as contact sheets; Kabir Idle front/back inspected at full resolution.',
 'observed':'Selected crew-neck geometry is present, but skin breaks through the chest, abdomen, shoulders and upper back. Other parts garments have no comparable broad holes in these views. White hair artifacts remain visible.',
 'reference_pose_diagnosis_pending':True,'live_config_changed':False,
 'limits':'Frozen actor LOD 0 poses only; no continuous movement, GPU crowd, all-LOD, complete-world, performance or fidelity acceptance.'}
write(folder/'VisualReview.json',review)
progress=BASE/'Progress.json';p=read(progress)
backup=BASE/'ProgressBeforeVerifiedLOD0_20260930.json';assert not backup.exists();shutil.copy2(progress,backup)
assert not any(f['family']=='G2PartsRetargetedLOD0' for f in p['candidate_families'])
p['candidate_families'].append({'family':'G2PartsRetargetedLOD0','body_source_lod_diagnostic':0,
 'saved_clones':len(build['instances']),'packages':len(build['new_packages']),'fresh_reload_pass':True,
 'animation_pose_comparisons':len(reload['animation_agreements']),'playback_metadata_comparisons':len(reload['metadata_agreements']),
 'reload_report':str(folder/'Reload.json'),'visual_review_report':str(folder/'VisualReview.json'),
 'visual_acceptance':False,'idle_walk_captures':24,'missing_selected_garment':False,
 'remaining_fit_issue':'Skin breaks through crew-neck shirt; reference-pose diagnosis pending.'})
p['saved_clones']=sum(f['saved_clones'] for f in p['candidate_families'])
p['new_packages']=sum(f['packages'] for f in p['candidate_families'])
p['native_tests']=record['native_tests'];p.pop('pending_native_changes',None)
p['current_build']={'candidate':'G2PartsRetargetedLOD0','state':'built_and_reloaded; reference_pose_review_running',
 'body_source_lod_diagnostic':0,'live_config_changed':False,'exec_session_id':2347}
p['remaining']='G2 crew-neck fit and hair repair; seven remaining G2-G5 clothing families and G6 animation review; actor/GPU/LOD/continuous/world integration, crowd spacing, exit stability; production campaign/inventory and complete gameplay; fresh cook/package/hardware controller/30 FPS minimum/60 FPS target acceptance. Full demo goal active.'
write(progress,p)
print(json.dumps({'saved_clones':p['saved_clones'],'packages':p['new_packages'],'native_tests':record['native_tests'],'visual_acceptance':False}))
