"""Place the three hospital campaign stations and prove them in PIE before saving.

Uses the verified approaches in HospitalStationApproachesDiagnosed_20260930.
Each station targets its real furnishing so the native focus trace ignores the
board/desk being read. Only the hospital set-dress sublevel is saved, after a
backup, and only if every station passes range, wall-free focus, story gate,
ordered native context dispatch and repeat guards in PIE.
"""
import hashlib,json,math,shutil,time,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
MAIN_MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
MAIN_FILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
LEVEL_NAME='L_IndustrialHospitalSetDress'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_IndustrialHospitalSetDress.umap'
APPROACHES=ROOT/'Saved/CampaignAcceptance/HospitalStationApproachesDiagnosed_20260930/index.json'
OUT=ROOT/'Saved/CampaignAcceptance/HospitalStationsAuthoredDeskTop_20260930';OUT.mkdir(parents=True,exist_ok=False)
# The records desk pivot is a floor-level corner, so a native trace to pivot+40
# crosses chairs and the counter. That station focuses on itself at the desk-top centre.
DESK_TOP=ROOT/'Saved/CampaignAcceptance/HospitalRecordsDeskTopFocus_20260930/index.json'
SELF_FOCUS={'hospital_records'}
ITEMS={'hospital_reception':'VisitingPass','hospital_ward':'EliAccount','hospital_records':'UtilityChart'}
REPORT={'success':False,'errors':[],'saved_level_modified':False,'stations':[],
 'limits':'PIE teleport to verified approaches with native focus/dispatch. Does not establish walked routes, rendered readability, physical controller input, cooked play or performance.'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write():(OUT/'index.json').write_text(json.dumps(REPORT,indent=2,default=str))
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT['main_map_sha256_before']=sha(MAIN_FILE);REPORT['level_sha256_before']=sha(LEVEL_FILE)
world=unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP);assert world
approaches=json.loads(APPROACHES.read_text());assert approaches['success']
in_level=lambda a:LEVEL_NAME+'.'+LEVEL_NAME+':' in a.get_path_name()
actors=[a for a in EA.get_all_level_actors() if in_level(a)]
assert LE.set_current_level_by_name(LEVEL_NAME),'Could not make the set-dress level current'
placed=[]
for s in approaches['stations']:
 label='Campaign_'+s['station']
 target=next(a for a in actors if a.get_actor_label()==s['furnishing'])
 location=unreal.Vector(*s['clue_world_cm'])
 if s['station'] in SELF_FOCUS:
  desk=json.loads(DESK_TOP.read_text());assert desk['success']
  location=unreal.Vector(*desk['station_world_cm']);target=None
 approach=unreal.Vector(*s['approach_world_cm'])
 reach=(approach-(target.get_actor_location() if target else location)).length()
 # Focus distance is measured to the target's pivot; keep a margin for capsule settling.
 radius=max(s['interaction_radius_cm'],math.ceil(reach+60))
 station=next((a for a in actors if a.get_actor_label()==label),None)
 created=station is None
 if created:station=EA.spawn_actor_from_class(unreal.CarnivalMissionInteractionActor,location)
 assert station and in_level(station),'Station actor must live in the set-dress level'
 station.set_actor_location(location,False,True);station.set_actor_label(label);station.set_folder_path('Campaign/After the music')
 station.set_editor_property('interaction',unreal.CarnivalMissionInteraction.CAMPAIGN_STATION)
 station.set_editor_property('campaign_station_id',s['station'])
 station.set_editor_property('interaction_target_actor',target)
 station.set_editor_property('interaction_radius',float(radius))
 station.set_editor_property('world_label_text',unreal.Text(''))
 placed.append({'label':label,'station':s['station'],'target':target.get_actor_label() if target else label,'approach':approach,
  'radius_cm':radius,'approach_to_target_cm':reach,'created':created})
REPORT['stations']=[{k:(list(v.to_tuple()) if isinstance(v,unreal.Vector) else v) for k,v in p.items()} for p in placed]
S={'phase':'wait','busy':False,'deadline':time.monotonic()+240}
def finish(error=None):
 if error:REPORT['errors'].append(error)
 REPORT['pie_success']=not REPORT['errors']
 write();LE.editor_request_end_play();S.update(phase='ending',deadline=time.monotonic()+20)
def save_or_revert():
 editor=[a for a in EA.get_all_level_actors() if in_level(a)]
 if REPORT.get('pie_success'):
  backup=OUT/('L_IndustrialHospitalSetDress.before_campaign_stations_'+time.strftime('%Y%m%d_%H%M%S')+'.umap')
  shutil.copy2(LEVEL_FILE,backup);REPORT['backup']=str(backup)
  level=next(a for a in editor if a.get_actor_label()==placed[0]['label']).get_outermost()
  if unreal.EditorLoadingAndSavingUtils.save_packages([level],False):
   REPORT['saved_level_modified']=True;REPORT['success']=True
  else:REPORT['errors'].append('Level package save returned false')
 else:
  for p in placed:
   a=next((a for a in editor if a.get_actor_label()==p['label']),None)
   if p['created'] and a:EA.destroy_actor(a)
 REPORT['main_map_sha256_after']=sha(MAIN_FILE);REPORT['level_sha256_after']=sha(LEVEL_FILE)
 if REPORT['main_map_sha256_after']!=REPORT['main_map_sha256_before']:
  REPORT['success']=False;REPORT['errors'].append('Persistent map changed unexpectedly')
 write();unreal.log('HOSPITAL_CAMPAIGN_STATIONS '+json.dumps({'success':REPORT['success'],'errors':REPORT['errors']}))
 unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
def stand(player,p,station):
 player.get_movement_component().stop_movement_immediately()
 player.set_actor_location(p,False,True)
 focus=station.get_editor_property('interaction_target_actor') or station
 d=focus.get_actor_location()-p
 player.set_actor_rotation(unreal.Rotator(yaw=math.degrees(math.atan2(d.y,d.x))),True)
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic();game=unreal.EditorLevelLibrary.get_game_world()
  if S['phase']=='ending':
   if not game or now>S['deadline']:save_or_revert()
   return
  if now>S['deadline']:raise RuntimeError('Timeout in '+S['phase'])
  if not game:return
  player=unreal.GameplayStatics.get_player_pawn(game,0)
  if not isinstance(player,unreal.CarnivalPlayerCharacter):return
  gi=unreal.GameplayStatics.get_game_instance(game)
  mission=next(o for o in unreal.ObjectIterator(unreal.CarnivalMissionSubsystem) if o.get_outer()==gi)
  campaign=next(o for o in unreal.ObjectIterator(unreal.CarnivalCampaignSubsystem) if o.get_outer()==gi)
  bylabel={a.get_actor_label():a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CarnivalMissionInteractionActor)}
  first=bylabel[placed[0]['label']]
  stand(player,placed[0]['approach'],first)
  assert not first.can_interact(player),'Sequel must stay locked before the rescue'
  # Opening-story prerequisite via its guarded API; the mansion journey is covered elsewhere.
  for m in ('begin_story_mission','report_mansion_arrival','collect_foyer_glove','collect_study_log_and_key',
    'report_worker_found','recover_music_box','report_doll_scare_complete','report_mansion_escaped','report_carnival_returned'):
   assert getattr(mission,m)(),m
  results=[]
  for i,p in enumerate(placed):
   station=bylabel[p['label']];r={'station':p['station']}
   stand(player,p['approach']+unreal.Vector(900,0,0),station)
   r['distant_blocked']=not station.can_interact(player)
   stand(player,p['approach'],station)
   r['player_location']=list(player.get_actor_location().to_tuple())
   focus=player.find_nearby_mission_interaction()
   r['focus']=focus.get_actor_label() if focus else None
   r['can_interact']=station.can_interact(player)
   player.try_context_interact()
   r['completed_after']=campaign.capture().completed_stations
   r['item_after']=campaign.get_item_count(ITEMS[p['station']])
   player.try_context_interact()
   r['repeat_guard']=campaign.capture().completed_stations==i+1
   results.append(r)
   assert r['distant_blocked'] and r['focus']==p['label'] and r['can_interact'],json.dumps(r)
   assert r['completed_after']==i+1 and r['item_after']==1 and r['repeat_guard'],json.dumps(r)
  REPORT['pie_results']=results;REPORT['journal_lines']=[str(x) for x in campaign.get_journal_lines()]
  finish()
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
write();handle=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
