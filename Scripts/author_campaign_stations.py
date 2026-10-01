"""Place the reachable campaign stations from StationSites7 and prove the whole chain in PIE.

Spawns collidable props and self-focusing station actors in each region's level.
PIE then plays all 17 stations in order: the hospital and every placed station
through the real character's native context interaction (with distance and
wrong-order guards), and the stations without a reachable site through the
campaign API only, recorded as such. Each touched level is backed up and saved
only if the whole proof passes; otherwise every spawned actor is removed.
"""
import hashlib,json,math,shutil,time,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
MAIN_MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
SITES=ROOT/'Saved/CampaignAcceptance/StationSites21_20261001/index.json'
OUT=ROOT/'Saved/CampaignAcceptance/CampaignStationsAuthored5_20261001';OUT.mkdir(parents=True,exist_ok=False)
ORDER=['hospital_reception','hospital_ward','hospital_records','wetlands_markers','bridge_relay','slums_workshop',
 'prison_archive','lab_a_calibration','lab_b_chart','sewer_route','north_docks_manifest','east_docks_dispatch',
 'shipwreck_manifest','atlantis_cradle','lab_b_remote','mansion_receiver','carnival_restoration']
SEQUENCE={'wetlands_markers':'123','bridge_relay':'231','lab_a_calibration':'213','sewer_route':'123',
 'atlantis_cradle':'321','lab_b_remote':'123','mansion_receiver':'312'}
HOSPITAL=ROOT/'Saved/CampaignAcceptance/HospitalStationsAuthoredDeskTop_20260930/index.json'
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V=unreal.Vector
REPORT={'success':False,'errors':[],'saved_levels':[],'placed':[],'api_only_stations':[],'pie':[],
 'limits':'PIE teleports to verified stand nodes and uses native focus/dispatch. Stand nodes are reachable from each region anchor by collision probe; anchor-to-anchor travel, rendered readability, physical controller input, cooked play and performance are not established.'}
def write():(OUT/'index.json').write_text(json.dumps(REPORT,indent=1,default=str))
def level_file(level):
 pkg=level.get_outermost().get_name()
 return ROOT/('Content'+pkg[len('/Game'):]+'.umap')
sites=json.loads(SITES.read_text())
hospital=json.loads(HOSPITAL.read_text());assert hospital['success']
world=unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP);assert world
levels={l.get_outermost().get_name().split('/')[-1]:l for l in unreal.EditorLevelUtils.get_levels(world)}
hashes_before={}
placed={};spawned=[];replaced=set();removed=[]
# A station being re-placed has its earlier actors (station + prop) removed first; the level
# backup taken before saving restores them if the proof fails.
for row in sites['stations']:
 for a in EA.get_all_level_actors():
  l=a.get_actor_label()
  if l=='Campaign_'+row['station'] or l.startswith('Campaign_'+row['station']+'_'):
   removed.append(l);replaced.add(row['station']);hashes_before.setdefault(row['level'],hashlib.sha256(level_file(levels[row['level']]).read_bytes()).hexdigest());EA.destroy_actor(a)
REPORT['removed_for_replacement']=removed
existing_labels={a.get_actor_label() for a in EA.get_all_level_actors()}
for row in sites['stations']:
 if row['errors']:REPORT['api_only_stations'].append({'station':row['station'],'reason':row['errors'][0].strip().splitlines()[-1]});continue
 level=levels[row['level']];f=level_file(level);hashes_before.setdefault(row['level'],hashlib.sha256(f.read_bytes()).hexdigest())
 assert LE.set_current_level_by_name(row['level']),row['level']
 multi=len(row['controls'])>1;actors=[]
 for c in row['controls']:
  suffix='_%d'%c['action'] if multi else ''
  label='Campaign_'+row['station']+suffix
  assert label not in existing_labels,'Station already placed: '+label
  if 'prop' in c and 'actor' not in c:
   mesh=unreal.load_asset(c['prop']);scale=c.get('prop_scale',1.);b=mesh.get_bounds()
   loc=c['prop_location'];bottom=(b.origin.z-b.box_extent.z)*scale
   prop=EA.spawn_actor_from_class(unreal.StaticMeshActor,V(loc[0],loc[1],loc[2]-bottom),unreal.Rotator(0,0,c['prop_yaw']))
   prop.static_mesh_component.set_static_mesh(mesh);prop.set_actor_scale3d(V(scale,scale,scale))
   prop.static_mesh_component.set_collision_profile_name('BlockAll')
   prop.set_actor_label(label+'_Prop');prop.set_folder_path('Campaign/'+row['station']);spawned.append(prop)
  # Face the stand so the 1/2/3 label reads correctly from where the player uses it.
  face=math.degrees(math.atan2(c['stand'][1]-c['station'][1],c['stand'][0]-c['station'][0]))
  st=EA.spawn_actor_from_class(unreal.CarnivalMissionInteractionActor,V(*c['station']),unreal.Rotator(0,0,face))
  st.set_actor_label(label);st.set_folder_path('Campaign/'+row['station']);spawned.append(st)
  st.set_editor_property('interaction',unreal.CarnivalMissionInteraction.CAMPAIGN_STATION)
  st.set_editor_property('campaign_station_id',row['station'])
  st.set_editor_property('campaign_action',c['action'])
  stand=V(*c['stand']);radius=math.ceil((stand-V(*c['station'])).length()+60)
  st.set_editor_property('interaction_radius',float(radius))
  st.set_editor_property('world_label_text',unreal.Text(str(c['action']) if multi else ''))
  st.set_editor_property('world_label_offset',V(0,0,45));st.set_editor_property('world_label_size',36.)
  if c.get('visual'):st.set_editor_property('interaction_mesh',unreal.load_asset(c['visual']))
  assert row['level'] in st.get_path_name(),'Station must live in its region level'
  actors.append({'label':label,'action':c['action'],'stand':stand,'radius':radius})
 placed[row['station']]=actors
 REPORT['placed'].append({'station':row['station'],'level':row['level'],'actors':[{k:(list(v.to_tuple()) if isinstance(v,V) else v) for k,v in a.items()} for a in actors]})
# Stations saved by the earlier pass (Lab A's were removed before the level-rotation fix).
# Stations saved by earlier passes; a later pass overrides an earlier one. Stations being
# re-placed now were removed above and are already in `placed`.
for name in ('CampaignStationsAuthored2_20260930','CampaignStationsAuthored3_20260930','CampaignStationsAuthored4_20260930'):
 for prow in json.loads((ROOT/'Saved/CampaignAcceptance'/name/'index.json').read_text())['placed']:
  if prow['station'] in replaced or (name.endswith('2_20260930') and prow['station']=='lab_a_calibration'):continue
  placed[prow['station']]=[{'label':a['label'],'action':a['action'],'stand':V(*a['stand']),'radius':a['radius']} for a in prow['actors']]
for h in hospital['stations']:placed[h['station']]=[{'label':h['label'],'action':0,'stand':V(*h['approach']),'radius':h['radius_cm']}]
write()
S={'phase':'wait','busy':False,'deadline':time.monotonic()+300}
def finish(error=None):
 if error:REPORT['errors'].append(error)
 REPORT['pie_success']=not REPORT['errors'];write()
 LE.editor_request_end_play();S.update(phase='ending',deadline=time.monotonic()+30)
def save_or_revert():
 if REPORT.get('pie_success'):
  for name,before in hashes_before.items():
   level=levels[name];f=level_file(level)
   assert hashlib.sha256(f.read_bytes()).hexdigest()==before,'Level changed on disk during authoring: '+name
   backup=OUT/'Backups'/(f.stem+'.before_campaign_stations.umap');backup.parent.mkdir(exist_ok=True);shutil.copy2(f,backup)
   if not unreal.EditorLoadingAndSavingUtils.save_packages([level.get_outermost()],False):
    REPORT['errors'].append('Save failed: '+name);continue
   REPORT['saved_levels'].append({'level':name,'backup':str(backup),'sha256_before':before,'sha256_after':hashlib.sha256(f.read_bytes()).hexdigest()})
  REPORT['success']=not REPORT['errors']
 else:
  for a in spawned:
   if a:EA.destroy_actor(a)
  REPORT['spawned_actors_removed']=True
 write();unreal.log('CAMPAIGN_STATIONS '+json.dumps({'success':REPORT['success'],'errors':REPORT['errors'][-1:]}))
 unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
def stand(player,p,target):
 player.get_movement_component().stop_movement_immediately()
 player.set_actor_location(p,False,True)
 d=target.get_actor_location()-p
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
  for m in ('begin_story_mission','report_mansion_arrival','collect_foyer_glove','collect_study_log_and_key',
    'report_worker_found','recover_music_box','report_doll_scare_complete','report_mansion_escaped','report_carnival_returned'):
   assert getattr(mission,m)(),m
  for index,station in enumerate(ORDER):
   r={'station':station,'steps':[]}
   if station not in placed:
    seq=SEQUENCE.get(station,'0')
    for ch in seq:assert campaign.use_station(station,int(ch)),station
    r['mode']='api_only';REPORT['pie'].append(r);assert campaign.capture().completed_stations==index+1,station;continue
   r['mode']='native_context';actors={a['action']:a for a in placed[station]}
   seq=SEQUENCE.get(station,'0')
   if len(seq)==3:
    # A wrong first control keeps progress and the quest item.
    wrong=next(a for a in (1,2,3) if str(a)!=seq[0]);a=actors[wrong];act=bylabel[a['label']]
    stand(player,a['stand'],act);assert player.find_nearby_mission_interaction()==act,'Focus on wrong-order control '+a['label']
    player.try_context_interact();r['wrong_order_kept_progress']=campaign.capture().completed_stations==index
    assert r['wrong_order_kept_progress'],station
   for ch in seq:
    a=actors[int(ch)];act=bylabel[a['label']]
    stand(player,a['stand']+V(a['radius']+600,0,0),act)
    far=not act.can_interact(player)
    stand(player,a['stand'],act)
    focus=player.find_nearby_mission_interaction()
    step={'label':a['label'],'distant_blocked':far,'focus':focus.get_actor_label() if focus else None,
     'player_location':list(player.get_actor_location().to_tuple())}
    player.try_context_interact();step['completed_after']=campaign.capture().completed_stations
    r['steps'].append(step)
    assert far and step['focus']==a['label'],json.dumps(step)
   assert campaign.capture().completed_stations==index+1,'%s did not complete: %s'%(station,campaign.last_result)
   stand(player,actors[int(seq[-1])]['stand'],bylabel[actors[int(seq[-1])]['label']]);player.try_context_interact()
   r['repeat_guard']=campaign.capture().completed_stations==index+1;assert r['repeat_guard'],station
   REPORT['pie'].append(r);write()
  REPORT['campaign_complete']=campaign.is_complete();assert REPORT['campaign_complete']
  REPORT['keepsake']=campaign.get_item_count('CarnivalKeepsake');assert REPORT['keepsake']==1
  finish()
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
write();handle=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
