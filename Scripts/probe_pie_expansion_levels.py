"""PIE: which expansion levels are loaded/visible, their actor counts, and floor traces at known points; no saves."""
import json,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CampaignAcceptance/PIEExpansionLevels_20260930';OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
PTS={'lab_a_pad':(-40750,-8350),'lab_a_interior':(-41900,-6700),'prison_tower':(-25900,-34360),'atlantis':(-13000,-11000),'docks_east':(70000,15000)}
R={'success':False,'errors':[],'levels':[],'traces':{}}
S={'busy':False,'deadline':time.monotonic()+200,'phase':'wait'}
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['deadline']:unreal.unregister_slate_post_tick_callback(h);unreal.SystemLibrary.quit_editor()
   return
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game or not unreal.GameplayStatics.get_player_pawn(game,0):
   if now>S['deadline']:raise RuntimeError('timeout')
   return
  if S['phase']=='wait':S.update(phase='settle',until=now+5);return
  if S['phase']=='settle' and now<S['until']:return
  actors=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
  counts={}
  for a in actors:
   lv=a.get_level().get_outermost().get_name().split('/')[-1] if a.get_level() else '?'
   counts[lv]=counts.get(lv,0)+1
  R['actor_counts_by_level_package']=dict(sorted(counts.items()))
  for name,(x,y) in PTS.items():
   hr=unreal.SystemLibrary.line_trace_single(game,unreal.Vector(x,y,3000),unreal.Vector(x,y,-3000),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
   t=hr.to_tuple() if hr else None
   R['traces'][name]={'hit':bool(t and t[0]),'z':t[5].z if t and t[0] else None,'actor':t[9].get_actor_label() if t and t[0] and t[9] else None}
  R['success']=True;(OUT/'index.json').write_text(json.dumps(R,indent=1))
  LE.editor_request_end_play();S.update(phase='exit',deadline=now+5)
 except Exception:
  R['errors'].append(traceback.format_exc());(OUT/'index.json').write_text(json.dumps(R,indent=1));LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+5)
 finally:S['busy']=False
h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
