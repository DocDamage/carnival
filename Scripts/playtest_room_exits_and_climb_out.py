"""PIE: can the real character leave the hospital rooms the grid audit still calls traps (open the door, walk
through), and climb out of the river at the North Dock boarding float and walk up the boat ramp? No saves."""
import json,math,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion/RoomExitsClimbOut_20261001';OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
V=unreal.Vector;FLOOR=643.0
DOORS=[('room_A',(95685,130876),'BP_Door_01a24'),('room_A',(95685,130876),'BP_Door_01a10'),
 ('room_C',(97007,124012),'BP_Door_01a28'),('room_C',(97007,124012),'BP_Door_01a29'),('room_C',(97007,124012),'BP_Door_02a6'),
 ('corridor',(96870,129436),'BP_Door_02a2')]
R={'success':False,'errors':[],'doors':[],'climb':None}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+600,'i':0}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'];save();LE.editor_request_end_play();S.update(phase='exit',until=time.monotonic()+5)
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
  mv=p.get_movement_component()
  if S['phase']=='wait':S.update(phase='door');return
  if S['phase']=='door':
   if S['i']>=len(DOORS):S.update(phase='climb');return
   room,(rx,ry),dl=DOORS[S['i']]
   d=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor) if a.get_actor_label()==dl),None)
   fr=[k for k in d.get_components_by_class(unreal.StaticMeshComponent) if k.static_mesh and 'Frame' in k.static_mesh.get_name()]
   fo=unreal.SystemLibrary.get_component_bounds(fr[0])[0]
   f=d.get_actor_forward_vector();f.z=0;f=f.normal()
   # Start on the room's side of the doorway, walk out through it.
   sg=1 if (V(rx,ry,0)-V(fo.x,fo.y,0)).dot(f)>0 else -1
   st=V(fo.x,fo.y,FLOOR+100)+f*(140*sg);dirv=f*(-sg)
   mv.stop_movement_immediately();p.set_actor_location(st,False,True)
   p.set_actor_rotation(unreal.Rotator(roll=0.0,pitch=0.0,yaw=math.degrees(math.atan2(dirv.y,dirv.x))),True)
   S.update(phase='door_open',until=now+0.5,rec={'room':room,'door':dl,'start':[round(v) for v in st.to_tuple()]},o=V(fo.x,fo.y,FLOOR),dirv=dirv,d=d);return
  if S['phase']=='door_open' and now>S['until']:
   S['rec']['nearby_door']=p.find_nearby_door().get_actor_label() if p.find_nearby_door() else None
   p.try_context_interact();S.update(phase='door_walk',until=now+4.5,t0=now+0.8);return
  if S['phase']=='door_walk':
   if now>S['t0']:p.add_movement_input(S['dirv'],1.0,True)
   if now>S['until']:
    d1=(p.get_actor_location()-S['o']).dot(S['dirv'])
    S['rec'].update(end=[round(v) for v in p.get_actor_location().to_tuple()],beyond_frame_cm=round(d1),passed=d1>120)
    R['doors'].append(S['rec']);save();S.update(phase='door',i=S['i']+1)
   return
  if S['phase']=='climb':
   # Swim at the surface south of the boarding float and push north onto it, then up the ramp.
   mv.stop_movement_immediately();p.set_actor_location(V(-50300,-58300,-320),False,True)
   p.set_actor_rotation(unreal.Rotator(roll=0.0,pitch=0.0,yaw=90.0),True)
   mv.set_movement_mode(unreal.MovementMode.MOVE_SWIMMING)
   S.update(phase='climb_go',until=now+20,t0=now+1.5,samples=[]);return
  if S['phase']=='climb_go':
   if now>S['t0']:p.add_movement_input(V(0,1,0),1.0,True)
   if len(S['samples'])<400 and int(now*4)!=S.get('last'):S['last']=int(now*4);S['samples'].append([round(v) for v in p.get_actor_location().to_tuple()]+[str(mv.movement_mode).split('.')[-1].split(':')[0]])
   if now>S['until']:
    z=[s[2] for s in S['samples']]
    R['climb']={'max_z':max(z),'end':S['samples'][-1],'reached_pier':max(z)>700,'out_of_water':any(s[2]>-150 and s[3]=='MOVE_WALKING' for s in S['samples']),'samples':S['samples'][::4]}
    finish()
   return
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
