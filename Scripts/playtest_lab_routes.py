"""PIE: try several walking routes from Lab A's entry room into the main room/Lab B; record progress and stalls. No saves."""
import json,math,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CampaignAcceptance/LabRoutes_20260930';OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
START=unreal.Vector(-41300,-7600,700)
ROUTES={'north_center':[(-41450,-7000),(-41500,-6500),(-41600,-6300),(-41900,-6100)],
 'north_east':[(-41100,-7000),(-41050,-6600),(-41100,-6200),(-41400,-6000),(-41900,-6000)],
 'west':[(-41700,-7300),(-42100,-7000),(-42300,-6700),(-42300,-6300)],
 'north_west':[(-41600,-7100),(-41800,-6700),(-42000,-6400),(-42200,-6100)],
 'far_east':[(-40900,-7300),(-40850,-6600),(-40900,-6000),(-41300,-5700)]}
R={'success':False,'errors':[],'routes':{},'assets_saved':False}
S={'phase':'load','busy':False,'deadline':time.monotonic()+400,'names':list(ROUTES),'i':0}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+5)
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
   if S['i']>=len(S['names']):R['success']=True;finish();return
   p.get_movement_component().stop_movement_immediately();p.set_actor_location(START,False,True)
   name=S['names'][S['i']];R['routes'][name]={'waypoints':ROUTES[name],'samples':[],'reached':0}
   S.update(phase='walk',name=name,wp=0,t0=now,last=now,lastpos=p.get_actor_location(),stall=0);return
  name=S['name'];wps=ROUTES[name];loc=p.get_actor_location();r=R['routes'][name]
  tx,ty=wps[S['wp']];d=unreal.Vector(tx-loc.x,ty-loc.y,0)
  if d.length()<70:
   S['wp']+=1;r['reached']=S['wp']
   if S['wp']>=len(wps):r['complete']=True;S.update(phase='load',i=S['i']+1);save();return
  else:p.add_movement_input(d.normal(),1.0,True)
  if now-S['last']>.4:
   moved=(loc-S['lastpos']).length();S['stall']=S['stall']+1 if moved<15 else 0
   S.update(last=now,lastpos=loc);r['samples'].append([round(loc.x),round(loc.y),round(loc.z)])
   if S['stall']>=5 or loc.z<300 or now-S['t0']>30:
    r['complete']=False;r['stopped_at']=[round(loc.x),round(loc.y),round(loc.z)];r['stopped_before_waypoint']=S['wp']
    hr=unreal.SystemLibrary.capsule_trace_single(game,loc,loc+d.normal()*60,40,90,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[p],unreal.DrawDebugTrace.NONE,True)
    t=hr.to_tuple() if hr else None
    r['blocker']=(t[9].get_actor_label() if t[9] else '')+'/'+(t[10].get_name() if t[10] else '') if t and t[0] else None
    S.update(phase='load',i=S['i']+1);save()
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
