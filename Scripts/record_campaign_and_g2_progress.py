"""Record verified evidence only; never mark the full demo accepted."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(r'F:\Carnival');BASE=ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930'
campaign=ROOT/'Saved/CampaignAcceptance/SignalNetwork_20260930'
tests=json.loads((campaign/'NativeRegression.json').read_text(encoding='utf-8-sig'))
assert tests['succeeded']==40 and not any(tests.get(k,0) for k in ('failed','notRun','inProcess','succeededWithWarnings'))
render=ROOT/'Saved/CampaignAcceptance/SignalNetworkRenderedGuardedStory_20260930'
proof=json.loads((render/'index.json').read_text());assert proof['fixture_success'] and not proof['errors'] and len(proof['captures'])==5
source=ROOT/'Saved/CharacterRepairs/G2SelectedClothingSource_20260930/index.json'
source_proof=json.loads(source.read_text());assert source_proof['success'] and not source_proof['errors']
sourcefiles=[ROOT/'Source/CarnivalGame'/name for name in ('CarnivalCampaignSubsystem.h','CarnivalCampaignSubsystem.cpp','CarnivalCampaignTests.cpp','CarnivalSaveSubsystem.h','CarnivalSaveSubsystem.cpp','CarnivalSaveTests.cpp','CarnivalMissionInteractionActor.h','CarnivalMissionInteractionActor.cpp','CarnivalPlayerController.h','CarnivalPlayerController.cpp','CarnivalHUD.cpp')]
record={'success':False,'native_foundation_verified':True,'native_tests':{k:tests.get(k,0) for k in ('succeeded','succeededWithWarnings','failed','notRun','inProcess')},
 'editor_build_pass':True,'development_game_build_pass':True,'campaign_station_count':22,'supply_slots':8,'save_version':2,
 'legacy_save_version_1_readable':True,'rendered_fixture_report':str(render/'index.json'),'manually_inspected_captures':5,
 'production_stations_placed':False,'full_campaign_gameplay_accepted':False,'physical_controller_acceptance':False,
 'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sourcefiles},
 'remaining':'Production placement and signs, physical travel/return, reward and pickup persistence, supply effects and building costs, encounters, complete original story/hospital, hardware controls, all remaining demo requirements, fresh cook/package and measured 30 FPS minimum / 60 FPS target.'}
(campaign/'index.json').write_text(json.dumps(record,indent=2))
progress=BASE/'Progress.json';backup=BASE/'ProgressBeforeG2AndCampaign_20260930.json'
assert not backup.exists(),'Preserve earlier progress evidence'
shutil.copy2(progress,backup);p=json.loads(progress.read_text())
build=json.loads((BASE/'G2PartsRetargeted/index.json').read_text());reload=json.loads((BASE/'G2PartsRetargeted/Reload.json').read_text())
assert build['success'] and reload['success'] and not build['errors'] and not reload['errors']
families=p['candidate_families'];assert not any(f['family']=='G2PartsRetargeted' for f in families)
families.append({'family':'G2PartsRetargeted','saved_clones':len(build['instances']),'packages':len(build['new_packages']),
 'fresh_reload_pass':True,'animation_pose_comparisons':len(reload['animation_agreements']),
 'playback_metadata_comparisons':len(reload['metadata_agreements']),'reload_report':str(BASE/'G2PartsRetargeted/Reload.json'),
 'visual_acceptance':False,'missing_selected_garment':'Kabir crew-neck shirt; also absent in source assembly',
 'idle_walk_captures':24,'source_inspection_report':str(source)})
p['saved_clones']=sum(f['saved_clones'] for f in families);p['new_packages']=sum(f['packages'] for f in families)
p['native_tests']=record['native_tests'];p['campaign_foundation_report']=str(campaign/'index.json')
p['current_build']={'candidate':'G2PartsRetargetedLOD0','state':'building','body_source_lod_diagnostic':0,'live_config_changed':False}
p['prior_progress_backup']=str(backup)
p['remaining']='G2 selected crew-neck LOD diagnosis/rebuild; seven remaining G2-G5 clothing families and G6 animation review; hair, actor/GPU/LOD/continuous/world integration, crowd spacing, exit stability; production campaign/inventory and complete gameplay; fresh cook/package/hardware controller/30 FPS minimum/60 FPS target acceptance. Full demo goal active.'
progress.write_text(json.dumps(p,indent=2))
print(json.dumps({'saved_clones':p['saved_clones'],'new_packages':p['new_packages'],'native_tests':record['native_tests'],'full_acceptance':False}))
