"""PIE: walk the real character from the Lab A entrance pad through BP_MGate01 toward Lab A's interior; no saves."""
import json,math,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CampaignAcceptance/LabGateWalk3_20260930';OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
START=unreal.Vector(-40750,-8350,720);WAYPOINTS=[(-40986,-8021),(-41300,-7600),(-41600,-7100),(-41900,-6700)]
R={'success':False,'errors':[],'samples':[],'assets_saved':False}
S={'phase':'load','busy':False,'deadline':time.monotonic()+200,'wp':0}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+5)
def doors(game):
 g=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor) if a.get_actor_label().startswith('BP_MGate01')),None)
 if not g:return None
 return {c.get_name():[round(v) for v in c.get_editor_property('relative_location').to_tuple()] for c in g.get_components_by_class(unreal.StaticMeshComponent)}
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['deadline']:unreal.unregister_slate_post_tick_callback(h);unreal.SystemLibrary.quit_editor()
   return
  if now>S['deadline']:raise RuntimeError('timeout '+S['phase'])
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game:return
  p=unreal.GameplayStatics.get_player_pawn(game,0)
  if not isinstance(p,unreal.CarnivalPlayerCharacter):return
  if S['phase']=='load':
   p.get_movement_component().stop_movement_immediately();p.set_actor_location(START,False,True)
   R['doors_before']=doors(game);S.update(phase='walk',t0=now,last=now);save();return
  loc=p.get_actor_location()
  if S['wp']<len(WAYPOINTS):
   tx,ty=WAYPOINTS[S['wp']]
   d=unreal.Vector(tx-loc.x,ty-loc.y,0)
   if d.length()<80:S['wp']+=1
   else:p.add_movement_input(d.normal(),1.0,True)
  if now-S['last']>.5:
   S['last']=now;R['samples'].append({'t':round(now-S['t0'],1),'loc':[round(v) for v in loc.to_tuple()],'waypoint':S['wp'],'doors':doors(game)})
   save()
  if S['wp']>=len(WAYPOINTS):R['reached_interior']=True;R['success']=True;finish();return
  if now-S['t0']>25:R['reached_interior']=False;finish('Did not reach Lab A interior within 25 s; stopped at waypoint %d'%S['wp']);return
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
