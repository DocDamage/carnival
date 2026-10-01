"""PIE probe: does the real character enter swimming in the world's water? Records movement mode, water
state and depth at several spots, plus whether a swim slot animation plays. No saves."""
import json,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterRepairs/SwimmingProbe3_20261001';OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
SPOTS=[('north_dock_berth',(-49000,-58200,0)),('north_dock_open',(-52000,-60000,0)),('east_dock_water',(70000,10000,400)),
 ('wetland_river_1',(-12000,-20000,0)),('wetland_river_2',(-30000,-50000,0))]
V=unreal.Vector;R={'success':False,'errors':[],'spots':[]}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+300,'i':0}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'];save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+5)
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
  if S['phase']=='wait':S.update(phase='place');return
  if S['phase']=='place':
   if S['i']>=len(SPOTS):finish();return
   name,loc=SPOTS[S['i']]
   # Find the surface (water or ground) below the spot and drop the player just above it.
   hr=unreal.SystemLibrary.line_trace_single(game,V(loc[0],loc[1],3000),V(loc[0],loc[1],-3000),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[p],unreal.DrawDebugTrace.NONE,True).to_tuple()
   floor=hr[5].z if hr[0] else None
   p.get_movement_component().stop_movement_immediately();p.set_actor_location(V(loc[0],loc[1],(floor if floor is not None else loc[2])+300),False,True)
   S.update(phase='settle',until=now+4,rec={'spot':name,'xy':loc[:2],'surface_below':round(floor,1) if floor is not None else None,'surface_actor':hr[9].get_actor_label() if hr[0] and hr[9] else None,'samples':[]});return
  if S['phase']=='settle':
   mv=p.get_movement_component();loc=p.get_actor_location()
   vol=None
   try:
    pv=mv.get_physics_volume();vol=(pv.get_name(),bool(pv.get_editor_property('water_volume'))) if pv else None
   except Exception as e:vol='n/a '+str(e)[:60]
   S['rec']['samples'].append({'z':round(loc.z),'mode':str(mv.movement_mode),'is_swimming':mv.is_swimming(),'volume':vol,'locomotion':str(p.get_editor_property('locomotion_state'))})
   if now>=S['until']:R['spots'].append(S['rec']);save();S.update(phase='place',i=S['i']+1)
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
