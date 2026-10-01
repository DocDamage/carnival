"""Transient native station dispatch and HUD proof; no production map/save edits."""
import json, os, struct, time, traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CampaignAcceptance'/os.environ.get('CARNIVAL_CAMPAIGN_REPORT','SignalNetworkRendered_20260930')
OUT.mkdir(parents=True,exist_ok=False)
REPORT={'success':False,'fixture_success':False,'errors':[],'captures':[],
 'assets_saved':False,'user_saves_modified':False,'physical_input':False,
 'limits':'Transient Entry fixture, native character context dispatch and API menu selection. Does not establish production locations, travel, hardware input, complete campaign gameplay or performance.'}
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',unreal.CarnivalGameMode)
cube=unreal.load_asset('/Engine/BasicShapes/Cube')
floor=EA.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-25))
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(30,30,.5))
floor.static_mesh_component.set_collision_profile_name('BlockAll')
EA.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(0,0,100))
camera=EA.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(-400,400,300))
camera.set_actor_label('CampaignProofCamera')
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(100,0,80)),True)
EA.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,500),unreal.Rotator(-60,-30,0))
for i,station in enumerate(('hospital_reception','hospital_ward','hospital_records')):
 actor=EA.spawn_actor_from_class(unreal.CarnivalMissionInteractionActor,unreal.Vector(i*500+100,0,80))
 actor.set_actor_label('CampaignProof_'+station)
 actor.set_editor_property('interaction',unreal.CarnivalMissionInteraction.CAMPAIGN_STATION)
 actor.set_editor_property('campaign_station_id',station)
 actor.set_editor_property('interaction_radius',150.)
 actor.set_editor_property('world_label_text',unreal.Text(''))
blocker=EA.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(50,0,150))
blocker.set_actor_label('CampaignProofBlocker')
blocker.static_mesh_component.set_static_mesh(cube)
blocker.set_actor_scale3d(unreal.Vector(.15,3.,3.))
blocker.set_actor_enable_collision(False);blocker.set_actor_hidden_in_game(True)
SHOTS=[('Objective',False,False,0,1280,800),('InventorySummary',True,False,0,1280,800),
 ('InventoryQuest',True,False,5,1280,800),('JournalObjective',True,True,0,1280,800),
 ('JournalRecord',True,True,1,800,600)]
S={'phase':'setup','busy':False,'deadline':time.monotonic()+240,'index':0}
def save():
 REPORT['phase']=S['phase'];(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def finish(error=None):
 if error:REPORT['errors'].append(error)
 REPORT['fixture_success']=not REPORT['errors'] and len(REPORT['captures'])==len(SHOTS)
 save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+4)
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['deadline']:unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
   return
  if now>S['deadline']:raise RuntimeError('Timeout in '+S['phase'])
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game:return
  if S['phase']=='setup':
   pc=unreal.GameplayStatics.get_player_controller(game,0)
   player=unreal.GameplayStatics.get_player_pawn(game,0)
   if not isinstance(pc,unreal.CarnivalPlayerController) or not isinstance(player,unreal.CarnivalPlayerCharacter):return
   assert isinstance(pc.get_hud(),unreal.CarnivalHUD)
   gi=unreal.GameplayStatics.get_game_instance(game)
   mission=next(o for o in unreal.ObjectIterator(unreal.CarnivalMissionSubsystem) if o.get_outer()==gi)
   campaign=next(o for o in unreal.ObjectIterator(unreal.CarnivalCampaignSubsystem) if o.get_outer()==gi)
   actors=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
   bylabel={a.get_actor_label():a for a in actors}
   station=bylabel['CampaignProof_hospital_reception']
   player.get_movement_component().stop_movement_immediately()
   player.set_actor_location(unreal.Vector(0,0,100),False,True)
   assert not station.can_interact(player),'Sequel must be locked before rescue'
   # Establish the opening-story prerequisite through its public guarded API.
   # This fixture does not test the actual mansion journey or doll encounter.
   for method in ('begin_story_mission','report_mansion_arrival','collect_foyer_glove',
     'collect_study_log_and_key','report_worker_found','recover_music_box',
     'report_doll_scare_complete','report_mansion_escaped','report_carnival_returned'):
    assert getattr(mission,method)(),method
   assert station.can_interact(player),'Station should be reachable in the fixture'
   blocker=bylabel['CampaignProofBlocker'];blocker.set_actor_enable_collision(True)
   assert not station.can_interact(player),'A wall must block station interaction'
   blocker.set_actor_enable_collision(False)
   player.set_actor_location(unreal.Vector(-1000,0,100),False,True)
   assert not station.can_interact(player),'Distant station must not interact'
   player.set_actor_location(unreal.Vector(0,0,100),False,True)
   assert player.find_nearby_mission_interaction()==station,'Station must win native context focus'
   player.try_context_interact()
   assert campaign.capture().completed_stations==1 and campaign.get_item_count('VisitingPass')==1
   player.try_context_interact()
   assert campaign.capture().completed_stations==1 and campaign.get_item_count('VisitingPass')==1
   REPORT['dispatch']={'range_guard':True,'wall_guard':True,'story_gate':True,'native_context':True,'repeated_acquisition_guard':True}
   assert campaign.grant_supply('Timber',7)
   REPORT['inventory_lines']=[str(x) for x in campaign.get_inventory_lines()]
   REPORT['journal_lines']=[str(x) for x in campaign.get_journal_lines()]
   pc.set_view_target_with_blend(bylabel['CampaignProofCamera'],0)
   pc.set_editor_property('using_gamepad',True)
   unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
   S.update(pc=pc,phase='menu',ready=now+3);save();return
  if now<S.get('ready',0):return
  name,paused,journal,page,width,height=SHOTS[S['index']]
  if S['phase']=='menu':
   pc=S['pc']
   if bool(pc.get_editor_property('session_menu_open'))!=paused:pc.toggle_session_menu()
   pc.set_editor_property('session_records_open',paused)
   pc.set_editor_property('journal_tab',journal)
   pc.set_editor_property('records_page',page)
   S.update(phase='request',ready=now+2);return
  if S['phase']=='request':
   S['file']=OUT/(name+'.png');S['requested']=time.time()
   unreal.SystemLibrary.execute_console_command(game,f'HighResShot {width}x{height} filename="{S["file"].as_posix()}"')
   S.update(phase='capture',ready=now+.5);return
  if S['phase']=='capture':
   file=S['file']
   if not file.exists() or file.stat().st_mtime<S['requested']-1:return
   blob=file.read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(width,height)
   REPORT['captures'].append({'image':str(file),'resolution':[width,height],'paused':paused,'journal':journal,'page':page})
   S['index']+=1;save()
   if S['index']==len(SHOTS):finish()
   else:S.update(phase='menu')
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
handle=unreal.register_slate_post_tick_callback(tick);save();LE.editor_request_begin_play()
