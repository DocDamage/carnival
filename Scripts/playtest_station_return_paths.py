"""PIE: the real character walks each planned path (anchor -> stand) with movement input; records arrival or stall. No saves."""
import json,math,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CampaignAcceptance/StationWalkPIEReturn_20260930';OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
PATHS=[dict(p,waypoints=list(reversed(p['waypoints'])),start=p['waypoints'][-1],station=p['station']+'_return') for p in json.loads((ROOT/'Saved/CampaignAcceptance/StationWalkPaths_20260930.json').read_text())['paths'] if p['found']]
R={'success':False,'errors':[],'walks':[],'assets_saved':False,'limits':'Scripted movement input along a planned path; not physical controller input.'}
S={'phase':'load','busy':False,'deadline':time.monotonic()+900,'i':0}
V=unreal.Vector
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'] and all(w.get('arrived') for w in R['walks']) and len(R['walks'])==len(PATHS)
 save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+5)
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
  if S['phase']=='load':
   if S['i']>=len(PATHS):finish();return
   path=PATHS[S['i']];p.get_movement_component().stop_movement_immediately()
   p.set_actor_location(V(*path['start'])+V(0,0,5),False,True)
   w={'station':path['station'],'planned_m':path['length_m'],'waypoints':len(path['waypoints'])};R['walks'].append(w)
   S.update(phase='walk',wp=1,t0=now,last=now,lastpos=p.get_actor_location(),stall=0,trail=0.0);return
  path=PATHS[S['i']];w=R['walks'][-1];loc=p.get_actor_location()
  tx,ty,tz=path['waypoints'][S['wp']];d=V(tx-loc.x,ty-loc.y,0)
  final=S['wp']==len(path['waypoints'])-1
  if d.length()<(45 if final else 70):
   if final:
    w.update(arrived=True,seconds=round(now-S['t0'],1),end=[round(v) for v in loc.to_tuple()],end_z_error=round(loc.z-tz,1))
    S.update(phase='load',i=S['i']+1);save();return
   S['wp']+=1
  else:p.add_movement_input(d.normal(),1.0,True)
  if now-S['last']>.5:
   moved=(loc-S['lastpos']).length();S['trail']+=moved;S['stall']=S['stall']+1 if moved<20 else 0
   S.update(last=now,lastpos=loc)
   if S['stall']>=6 or loc.z<-3000:
    hr=unreal.SystemLibrary.capsule_trace_single(game,loc,loc+d.normal()*60,40,90,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[p],unreal.DrawDebugTrace.NONE,True)
    t=hr.to_tuple() if hr else None
    w.update(arrived=False,stalled_at=[round(v) for v in loc.to_tuple()],before_waypoint=S['wp'],
     blocker=((t[9].get_actor_label() if t[9] else '')+'/'+(t[10].get_name() if t[10] else '')) if t and t[0] else None)
    S.update(phase='load',i=S['i']+1);save()
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
