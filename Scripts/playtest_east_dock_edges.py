"""PIE: what is under and around the East Dock in the game world? Editor traces find nothing below the decks
(`probe_east_dock_boatyard_site.py`). For a set of points just off the deck edges, trace down in the game world and
drop the real character there; record where it lands (or that it keeps falling), and whether it can get back onto a
deck by Return to path. No saves."""
import json,math,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\EastDockEdgesPIE_v4_fallnet_20261001.json')
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);V=unreal.Vector
SPOTS=[('between_fingers_west',(68650,25000,720)),('between_fingers_east',(71350,25000,720)),('beyond_centre_finger_tip',(70000,31200,720)),
 ('quay_east_edge',(75000,15000,720)),('quay_south_edge',(70000,10800,720)),('quay_west_of_through_walk',(65200,13000,720)),
 ('finger_link_gap',(68650,20500,720)),('on_main_quay_control',(70000,18000,720))]
R={'success':False,'errors':[],'spots':[]}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+1200,'i':0}
def save():OUT.write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'] and len(R['spots'])==len(SPOTS);save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+5)
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['deadline']:unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
   return
  if now>S['deadline']:raise RuntimeError('timeout '+S['phase'])
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game:return
  p=unreal.GameplayStatics.get_player_pawn(game,0)
  if not isinstance(p,unreal.CarnivalPlayerCharacter):return
  gt=unreal.GameplayStatics.get_time_seconds(game);mv=p.get_movement_component()
  if S['phase']=='wait':
   unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
   R['kill_z']=game.get_world_settings().get_editor_property('kill_z');S.update(phase='place');return
  if S['phase']=='place':
   if S['i']>=len(SPOTS):finish();return
   name,loc=SPOTS[S['i']]
   hits=[];z=5000.0;skip=[p]
   for _ in range(5):
    h=unreal.SystemLibrary.line_trace_single(game,V(loc[0],loc[1],z),V(loc[0],loc[1],-20000),unreal.TraceTypeQuery.ECC_VISIBILITY,False,skip,unreal.DrawDebugTrace.NONE,True)
    h=h.to_tuple() if h else None
    if not h or not h[0]:break
    hits.append([h[9].get_actor_label() if h[9] else '',round(h[5].z)]);skip.append(h[9]);z=h[5].z-1
   # Stand on the Main Quay first so the safe point is on the dock, as when a player walks off an edge.
   mv.stop_movement_immediately();p.set_actor_location(V(70000,18000,760),False,True)
   S.update(phase='stand',until_g=gt+1.5,hits=hits);return
  if S['phase']=='stand':
   if gt<S['until_g']:return
   name,loc=SPOTS[S['i']];hits=S['hits']
   mv.stop_movement_immediately();p.set_actor_location(V(*loc),False,True)
   S.update(phase='fall',t0=gt,rec={'spot':name,'placed':loc,'game_traces':hits,'samples':[]},last=-9);return
  if S['phase']=='fall':
   r=S['rec'];pos=p.get_actor_location()
   if gt-S['last']>=0.5:r['samples'].append([round(gt-S['t0'],1),round(pos.z),str(mv.movement_mode).split('.')[-1].split(':')[0]]);S['last']=gt
   if gt-S['t0']>=6.0:
    r.update(end=[round(v) for v in pos.to_tuple()],walking=bool(mv.is_moving_on_ground()),fell_cm=round(r['placed'][2]-pos.z))
    floor=mv.current_floor.hit_result.to_tuple() if mv.is_moving_on_ground() else None
    r['floor_actor']=floor[9].get_actor_label() if floor and floor[9] else None
    ok=p.return_to_nearest_route();r['return_to_path']=ok;r['after_return']=[round(v) for v in p.get_actor_location().to_tuple()]
    R['spots'].append(r);save();S.update(phase='place',i=S['i']+1)
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
try:
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 save();handle=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
except Exception:R['errors'].append(traceback.format_exc());save();unreal.SystemLibrary.quit_editor()
