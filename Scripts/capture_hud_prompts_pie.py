"""Rendered PIE review of the Swimming and Locked HUD prompts (UI included via shot showui) (copied from capture_water_pie_v2.py): places the real character at the docks, in the river, in flooded Atlantis /
Shipwreck and at the sewer-tunnel waterline, records movement state, and captures the player camera. Also
re-walks the two rotated hospital double doors along their own facing. No saves."""
import json,math,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion/HudPromptsPIE_v2_20261001';OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
V=unreal.Vector
# name, player location, yaw, camera pitch, seconds to settle, held input (None/'up'/'down'), forward input
SHOTS=[
 ('00_Warmup_Swim',(-49000,-58200,0),90,-10,5,None,0),  # the first `shot` can grab the editor viewport
 ('01_Swim_NorthDock',(-49000,-58200,0),90,-10,5,None,0),
 ('02_Locked_Door02a2',(96880,129430,700),-36,-5,3,None,0),
]
DOORS=[]
R={'success':False,'errors':[],'shots':[],'doors':[]}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+900,'i':0,'d':0}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'];save();LE.editor_request_end_play();S.update(phase='exit',until=time.monotonic()+5)
def state(p):
 mv=p.get_movement_component();pv=mv.get_physics_volume()
 return {'loc':[round(v) for v in p.get_actor_location().to_tuple()],'mode':str(mv.movement_mode).split('.')[-1].split(':')[0],
  'volume':pv.get_actor_label() if pv else None,'water':bool(pv.get_editor_property('water_volume')) if pv else None,
  'submerged':p.is_submerged(),'seabed':p.is_seabed_walking(),'camera_underwater':p.is_camera_underwater(),
  'swim_anim':p.get_active_swim_animation().get_name() if p.get_active_swim_animation() else None}
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
   if S['i']>=len(SHOTS):S.update(phase='door');return
   name,loc,yaw,pitch,secs,hold,fwd=SHOTS[S['i']]
   p.set_swim_up_held(False);p.set_swim_down_held(False)
   p.get_movement_component().stop_movement_immediately()
   p.set_actor_location(V(*loc),False,True);p.set_actor_rotation(unreal.Rotator(roll=0.0,pitch=0.0,yaw=float(yaw)),True)
   pc.set_control_rotation(unreal.Rotator(roll=0.0,pitch=float(pitch),yaw=float(yaw)))
   p.get_movement_component().set_movement_mode(unreal.MovementMode.MOVE_FALLING)
   if hold=='up':p.set_swim_up_held(True)
   if hold=='down':p.set_swim_down_held(True)
   S.update(phase='settle',until=now+secs,fwd=fwd,rec={'name':name,'start':list(loc),'samples':[]});return
  if S['phase']=='settle':
   if S['fwd']:p.add_movement_input(p.get_actor_forward_vector(),S['fwd'],True)
   if len(S['rec']['samples'])<40:S['rec']['samples'].append(state(p))
   if now>=S['until']:
    path=OUT/(S['rec']['name']+'.png')
    unreal.SystemLibrary.execute_console_command(game,'shot showui')
    S['rec']['final']=state(p);S.update(phase='shot',until=now+6,path=path)
   return
  if S['phase']=='shot':
   if S['path'].exists() and S['path'].stat().st_size>10000 or now>S['until']:
    S['rec']['image']=str(S['path']) if S['path'].exists() else None
    S['rec']['samples']=S['rec']['samples'][::5]
    R['shots'].append(S['rec']);save();p.set_swim_up_held(False);p.set_swim_down_held(False)
    S.update(phase='place',i=S['i']+1,until=now+1)
   return
  if S['phase']=='door':
   if S['d']>=len(DOORS):finish();return
   d=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor) if a.get_actor_label()==DOORS[S['d']]),None)
   if not d:R['doors'].append({'door':DOORS[S['d']],'error':'not found'});S['d']+=1;return
   # Leaves span the door's local Y, so the passage normal is the door's forward axis.
   fr=[c for c in d.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh and 'Frame' in c.static_mesh.get_name()]
   o=unreal.SystemLibrary.get_component_bounds(fr[0])[0] if fr else d.get_actor_location()
   f=d.get_actor_forward_vector();f.z=0;f=f.normal()
   chosen=None
   for sg in (1,-1):
    st=o+f*(160*sg);st.z=o.z-20
    hit=unreal.SystemLibrary.capsule_trace_single(game,st,st+V(0,0,1),40,80,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[p],unreal.DrawDebugTrace.NONE,True)
    if not hit or not hit.to_tuple()[0]:chosen=(st,f*(-sg));break
   if not chosen:R['doors'].append({'door':DOORS[S['d']],'error':'no clear side'});S['d']+=1;return
   st,dirv=chosen
   p.get_movement_component().stop_movement_immediately();p.set_actor_location(st,False,True)
   p.set_actor_rotation(unreal.Rotator(roll=0.0,pitch=0.0,yaw=math.degrees(math.atan2(dirv.y,dirv.x))),True)
   p.try_context_interact()
   S.update(phase='door_walk',until=now+5,t_push=now+1,dirv=dirv,door=d,start=st,origin=o);return
  if S['phase']=='door_walk':
   if now>S['t_push']:p.add_movement_input(S['dirv'],1.0,True)
   if now>S['until']:
    o=S['origin'];d0=(S['start']-o).dot(S['dirv']);d1=(p.get_actor_location()-o).dot(S['dirv'])
    R['doors'].append({'door':S['door'].get_actor_label(),'start_side_cm':round(d0),'end_side_cm':round(d1),'crossed':d0<0 and d1>60})
    save();S.update(phase='door',d=S['d']+1)
   return
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();handle=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
