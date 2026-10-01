"""PIE: closed vendor doors open on context interact, and the real character then walks through. No saves."""
import json,math,os,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/os.environ.get('CARNIVAL_DOOR_SURVEY_OUT','Saved/WorldExpansion/VendorDoorsInteractPIE_20261001');OUT.mkdir(parents=True,exist_ok=False)
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
   def closed(d):
    ys=[c.get_editor_property('relative_rotation').yaw for c in d.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh and ('Door_Plate' in c.static_mesh.get_name() or c.static_mesh.get_name() in ('SM_Door02_D','SM_Door02_E'))]
    fr=[c.get_editor_property('relative_rotation').yaw for c in d.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh and 'Frame' in c.static_mesh.get_name()]
    f=fr[0] if fr else 0
    return ys and all(abs((y-f+180)%360-180)<5 for y in ys)
   pick=[];seen={}
   for d in allD:
    c=d.get_class().get_name()
    if closed(d) and seen.get(c,0)<2:pick.append(d);seen[c]=seen.get(c,0)+1
   S['doors']=pick;R['door_count_world']=len(allD);S['phase']='place';return
  if S['phase']=='place':
   if S['i']>=len(S['doors']):finish();return
   d=S['doors'][S['i']];o,e=d.get_actor_bounds(False)
   # Stand 1.5 m from the door along its thin axis, facing it.
   ax=V(1,0,0) if e.x<e.y else V(0,1,0)
   start=o+ax*150;start.z=o.z-e.z+100
   # Use whichever side of the doorway has open floor.
   for sg in (1,-1):
    st=o+ax*150*sg;st.z=o.z-e.z+100
    hit=unreal.SystemLibrary.capsule_trace_single(game,st+V(0,0,20),st+V(0,0,21),40,80,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[p],unreal.DrawDebugTrace.NONE,True)
    if not hit or not hit.to_tuple()[0]:start=st;ax=ax*sg;break
   p.get_movement_component().stop_movement_immediately();p.set_actor_location(start,False,True)
   look=o-start;p.set_actor_rotation(unreal.Rotator(yaw=math.degrees(math.atan2(look.y,look.x))),True)
   p.try_context_interact()
   S.update(phase='push',until=now+5.0,t_push=now+1.0,rec={'door':d.get_actor_label(),'class':d.get_class().get_name(),'level':d.get_level().get_outermost().get_name().split('/')[-1],'before':leaves(d),'start':list(start.to_tuple())},door=d,dirv=V(-ax.x,-ax.y,0));return
  if S['phase']=='push':
   if now>S['t_push']:p.add_movement_input(S['dirv'],1.0,True)
   if now>S['until']:S.update(phase='after',until=now)
   return
  if S['phase']=='after' and now>S['until']:
   r=S['rec'];r['after']=leaves(S['door']);r['moved']=r['after']!=r['before']
   r['player_end']=list(p.get_actor_location().to_tuple())
   o,e=S['door'].get_actor_bounds(False);d0=(V(*r['start'])-o).dot(S['dirv']);d1=(p.get_actor_location()-o).dot(S['dirv'])
   r['crossed_doorway']=d0<0<d1 and d1>60;r['player_moved_cm']=round((p.get_actor_location()-V(*r['start'])).length())
   R['doors'].append(r);save();S.update(phase='place',i=S['i']+1)
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
