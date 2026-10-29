"""Rendered PIE: what the player sees where editor and game traces find nothing under the walkable surface (the East
Dock and the OuterRoute spine between the East Dock and the Hospital, plus the mansion-driveway segments). Stands
the real character on the deck, looks out and down over the edge, and captures the player camera. No saves.
Run in `editor` mode (rendered)."""
import json,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\VoidAreasPIE_20261001');OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);V=unreal.Vector
# name, location (on the deck), yaw, camera pitch
SHOTS=[('01_EastDock_Quay_to_Fingers',(70000,17200,760),90,-20),('02_EastDock_Finger_Edge_Down',(70500,25000,780),0,-55),
 ('03_EastDock_Quay_South_Edge',(70000,11700,760),-90,-35),('04_Spine_Northeast_Side',(80485,67858,770),0,-35),
 ('05_Spine_Near_Hospital',(88602,106458,760),-170,-30),('06_Spine_Mansion_Driveway',(-68820,-83416,700),90,-35)]
R={'success':False,'errors':[],'shots':[]}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+600,'i':0}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'] and all(s.get('image') for s in R['shots']);save();LE.editor_request_end_play();S.update(phase='exit',until=time.monotonic()+5)
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['until']:unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
   return
  if now>S['deadline']:raise RuntimeError('timeout in '+S['phase'])
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game:return
  p=unreal.GameplayStatics.get_player_pawn(game,0)
  if not isinstance(p,unreal.CarnivalPlayerCharacter):return
  pc=unreal.GameplayStatics.get_player_controller(game,0)
  if S['phase']=='wait':S.update(phase='place',until=now+8);return
  if S['phase']=='place':
   if now<S['until']:return
   if S['i']>=len(SHOTS):finish();return
   name,loc,yaw,pitch=SHOTS[S['i']]
   p.get_movement_component().stop_movement_immediately();p.set_actor_location(V(*loc),False,True)
   p.set_actor_rotation(unreal.Rotator(roll=0.0,pitch=0.0,yaw=float(yaw)),True)
   pc.set_control_rotation(unreal.Rotator(roll=0.0,pitch=float(pitch),yaw=float(yaw)))
   S.update(phase='settle',until=now+5,rec={'name':name,'placed':list(loc)});return
  if S['phase']=='settle' and now>=S['until']:
   S['rec']['final']=[round(v) for v in p.get_actor_location().to_tuple()]
   S['rec']['walking']=bool(p.get_movement_component().is_moving_on_ground())
   path=OUT/(S['rec']['name']+'.png')
   unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x720 filename="'+str(path).replace('\\','/')+'"')
   S.update(phase='shot',until=now+20,path=path);return
  if S['phase']=='shot':
   if (S['path'].exists() and S['path'].stat().st_size>10000) or now>S['until']:
    S['rec']['image']=str(S['path']) if S['path'].exists() else None
    R['shots'].append(S['rec']);save();S.update(phase='place',i=S['i']+1,until=now+1)
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
try:
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for a in list(EA.get_all_level_actors()):
  if a.get_class().get_name()=='MetaHumanMassSpawner':EA.destroy_actor(a)
 save();handle=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
except Exception:R['errors'].append(traceback.format_exc());save();unreal.SystemLibrary.quit_editor()
