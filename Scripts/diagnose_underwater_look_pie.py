"""Rendered PIE diagnostic for the underwater look at Atlantis: records the view target / camera post-process
state, captures the player view, then captures again with the same material in an unbound post-process volume.
No saves."""
import json,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT=Path(r'F:\Carnival\Saved\CharacterRepairs\UnderwaterLookDiag_20261001');OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
V=unreal.Vector;R={'errors':[]};S={'phase':'wait','busy':False,'deadline':time.monotonic()+600}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 save();LE.editor_request_end_play();S.update(phase='exit',until=time.monotonic()+5)
def shot(game,name):
 p=OUT/(name+'.png');unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x720 filename="'+str(p).replace('\\','/')+'"');return p
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['until']:unreal.unregister_slate_post_tick_callback(h);unreal.SystemLibrary.quit_editor()
   return
  if now>S['deadline']:raise RuntimeError('timeout '+S['phase'])
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game:return
  p=unreal.GameplayStatics.get_player_pawn(game,0)
  if not isinstance(p,unreal.CarnivalPlayerCharacter):return
  pc=unreal.GameplayStatics.get_player_controller(game,0)
  if S['phase']=='wait':
   p.set_actor_location(V(-13500,-11000,-1600),False,True);pc.set_control_rotation(unreal.Rotator(roll=0.0,pitch=-10.0,yaw=0.0))
   S.update(phase='look',until=now+6);return
  if S['phase']=='look' and now>S['until']:
   cams=p.get_components_by_class(unreal.CameraComponent)
   R['pawn_class']=p.get_class().get_path_name()
   R['view_target']=pc.get_view_target().get_name() if pc.get_view_target() else None
   R['cameras']=[{'name':c.get_name(),'active':c.is_active(),'weight':c.get_editor_property('post_process_blend_weight'),
     'blendables':len(c.get_editor_property('post_process_settings').weighted_blendables.array),
     'loc':[round(v) for v in c.get_world_location().to_tuple()]} for c in cams]
   R['camera_manager_loc']=[round(v) for v in unreal.GameplayStatics.get_player_camera_manager(game,0).get_camera_location().to_tuple()]
   R['camera_underwater']=p.is_camera_underwater()
   S.update(phase='shot1',path=shot(game,'01_camera_pp'),until=now+20);return
  if S['phase']=='shot1' and (S['path'].exists() or now>S['until']):
   m=unreal.load_asset('/Game/Carnival/World/Materials/Water/M_CarnivalUnderwaterPP')
   R['material_loaded']=bool(m)
   v=unreal.EditorLevelLibrary.get_game_world().spawn_actor(unreal.PostProcessVolume,V(0,0,0),unreal.Rotator()) if hasattr(unreal.World,'spawn_actor') else None
   if v is None:
    v=unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(game,unreal.PostProcessVolume,unreal.Transform()) if hasattr(unreal.GameplayStatics,'begin_deferred_actor_spawn_from_class') else None
    if v:unreal.GameplayStatics.finish_spawning_actor(v,unreal.Transform())
   if v:
    v.set_editor_property('unbound',True)
    st=v.get_editor_property('settings');wb=unreal.WeightedBlendable();wb.weight=1.0;wb.object=m
    arr=unreal.WeightedBlendables();arr.array=[wb];st.weighted_blendables=arr;v.set_editor_property('settings',st)
    R['volume_spawned']=True
   S.update(phase='shot2wait',until=now+3);return
  if S['phase']=='shot2wait' and now>S['until']:
   S.update(phase='shot2',path=shot(game,'02_volume_pp'),until=now+20);return
  if S['phase']=='shot2' and (S['path'].exists() or now>S['until']):finish()
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
