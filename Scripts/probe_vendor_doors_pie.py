"""PIE: do vendor BP_Door actors open for the real character (walk into them, press interact)? No saves."""
import json,math,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion/VendorDoorsPIE_20261001';OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
V=unreal.Vector;R={'success':False,'errors':[],'doors':[]}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+400,'i':0,'doors':None}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'];save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+5)
def leaves(d):
 return {c.get_name():[round(v,2) for v in c.get_editor_property('relative_rotation').to_tuple()] for c in d.get_components_by_class(unreal.StaticMeshComponent)}
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['deadline']:unreal.unregister_slate_post_tick_callback(h);unreal.SystemLibrary.quit_editor()
   return
  if now>S['deadline']:raise RuntimeError('timeout')
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game:return
  p=unreal.GameplayStatics.get_player_pawn(game,0)
  if not isinstance(p,unreal.CarnivalPlayerCharacter):return
  if S['doors'] is None:
   allD=[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor) if a.get_actor_label().startswith('BP_Door')]
   pick=[d for d in allD if d.get_actor_label() in ('BP_Door_01a24','BP_Door_01a29','BP_Door_02a6')]
   mans=[d for d in allD if 'HauntedMansion' in d.get_level().get_outermost().get_name()][:2]
   S['doors']=pick+mans;R['door_count_world']=len(allD);S['phase']='place';return
  if S['phase']=='place':
   if S['i']>=len(S['doors']):finish();return
   d=S['doors'][S['i']];o,e=d.get_actor_bounds(False)
   # Stand 1.5 m from the door along its thin axis, facing it.
   ax=V(1,0,0) if e.x<e.y else V(0,1,0)
   start=o+ax*170;start.z=o.z-e.z+100
   p.get_movement_component().stop_movement_immediately();p.set_actor_location(start,False,True)
   look=o-start;p.set_actor_rotation(unreal.Rotator(yaw=math.degrees(math.atan2(look.y,look.x))),True)
   S.update(phase='push',until=now+3.0,rec={'door':d.get_actor_label(),'class':d.get_class().get_name(),'level':d.get_level().get_outermost().get_name().split('/')[-1],'before':leaves(d),'start':list(start.to_tuple())},door=d,dirv=V(-ax.x,-ax.y,0));return
  if S['phase']=='push':
   p.add_movement_input(S['dirv'],1.0,True)
   if now>S['until']:
    p.try_context_interact();S.update(phase='after',until=now+2.0)
   return
  if S['phase']=='after' and now>S['until']:
   r=S['rec'];r['after']=leaves(S['door']);r['moved']=r['after']!=r['before']
   r['player_end']=list(p.get_actor_location().to_tuple());r['player_moved_cm']=round((p.get_actor_location()-V(*r['start'])).length())
   R['doors'].append(r);save();S.update(phase='place',i=S['i']+1)
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
