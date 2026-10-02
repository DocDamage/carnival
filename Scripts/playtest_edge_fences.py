"""PIE: the edge fences hold. At a spread of the railings placed by `author_walkable_edge_fences.py` (farthest-point
sampling over all of them), stand the real character 1.5 m inside the railing, then run into it and jump every
second for 4 s. Pass = it never drops more than 1.5 m below where it started and ends walking. No saves."""
import json,math,os,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');SRC=ROOT/'Saved/WorldExpansion/WalkableEdgeFences_20261001/index.json'
OUT=ROOT/'Saved/WorldExpansion'/('EdgeFencesPIE'+os.environ.get('CARNIVAL_AUDIT_SUFFIX','_20261001')+'.json')
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);V=unreal.Vector
JUMP=os.environ.get('CARNIVAL_FENCE_JUMP','1')=='1'
fences=json.loads(SRC.read_text())['fences'];PICKS=int(os.environ.get('CARNIVAL_FENCE_PICKS','20'))
picks=[fences[0]]
while len(picks)<min(PICKS,len(fences)):picks.append(max(fences,key=lambda f:min(math.dist(f['at'],p['at']) for p in picks)))
for f in fences:   # always include every boatyard guard type at least once
 if f['guards'].startswith('EastDock') and f['guards'] not in {p['guards'] for p in picks}:picks.append(f)
R={'success':False,'errors':[],'tests':[]}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+120+len(picks)*40,'i':0}
def save():OUT.write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['passed']=sum(1 for t_ in R['tests'] if t_.get('pass'));R['count']=len(R['tests'])
 R['success']=not R['errors'] and R['count']==len(picks) and R['passed']==R['count'];save();LE.editor_request_end_play();S.update(phase='exit',until=time.monotonic()+5)
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['until']:unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
   return
  if now>S['deadline']:raise RuntimeError('timeout '+S['phase'])
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game:return
  p=unreal.GameplayStatics.get_player_pawn(game,0)
  if not isinstance(p,unreal.CarnivalPlayerCharacter):return
  gt=unreal.GameplayStatics.get_time_seconds(game);mv=p.get_movement_component()
  if S['phase']=='wait':
   c=p.get_controller()
   if c:c.set_ignore_move_input(False)
   unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
   S['fence_actors']=[a for a in unreal.GameplayStatics.get_all_actors_with_tag(game,'CarnivalEdgeFence')]
   R['fence_actors_in_game']=len(S['fence_actors']);S.update(phase='place');return
  if S['phase']=='place':
   if S['i']>=len(picks):finish();return
   f=picks[S['i']];at=V(*f['at'])
   fa=min(S['fence_actors'],key=lambda a:(a.get_actor_location()-at).length())
   x=fa.get_actor_forward_vector();x=V(x.x,x.y,0);x=x*(1.0/max(x.length(),1e-3))
   def floor(pt):
    h=unreal.SystemLibrary.line_trace_single(game,V(pt.x,pt.y,pt.z+200),V(pt.x,pt.y,pt.z-300),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[fa,p],unreal.DrawDebugTrace.NONE,True)
    h=h.to_tuple() if h else None;return h[5] if h and h[0] else None
   inward=None
   for sg in (1,-1):
    fl=floor(at+x*(150*sg))
    if fl:inward=x*sg;stand=fl+V(0,0,100);break
   if inward is None:R['tests'].append({'fence':f,'pass':False,'error':'no floor either side'});S['i']+=1;return
   mv.stop_movement_immediately();p.set_actor_location(stand,False,True)
   S.update(phase='settle',until_g=gt+1.0,rec={'fence':f,'stand':[round(v) for v in stand.to_tuple()]},inward=inward,lastjump=gt);return
  if S['phase']=='settle':
   if gt<S['until_g']:return
   S['rec']['start_z']=round(p.get_actor_location().z);S.update(phase='push',t0=gt,minz=p.get_actor_location().z);return
  if S['phase']=='push':
   out=S['inward']*-1.0;p.add_movement_input(out,1.0,True);z=p.get_actor_location().z;S['minz']=min(S['minz'],z)
   if JUMP and gt-S['lastjump']>=1.0:p.jump();S['lastjump']=gt
   if gt-S['t0']>=4.0:
    p.stop_jumping();r=S['rec'];end=p.get_actor_location()
    r.update(end=[round(v) for v in end.to_tuple()],min_z=round(S['minz']),walking_or_landing=bool(mv.is_moving_on_ground() or mv.is_falling()))
    r['pass']=bool(S['minz']>=r['start_z']-150 and abs(end.z-r['start_z'])<150)
    R['tests'].append(r);save();S.update(phase='place',i=S['i']+1)
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
try:
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for a in list(EA.get_all_level_actors()):
  if a.get_class().get_name()=='MetaHumanMassSpawner':EA.destroy_actor(a)
 R['picked']=len(picks);save();handle=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
except Exception:R['errors'].append(traceback.format_exc());save();unreal.SystemLibrary.quit_editor()
