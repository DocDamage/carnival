"""PIE: from awkward spots across the world, the real character's ReturnToNearestRoute lands on a clear,
walkable anchor and stays grounded. No saves.

CARNIVAL_RTP_SET=rides starts from the four spots where ride anchors used to be (inside the circus tent and the
haunted house, the Flying Bobs pit, the swing platform) and expects the relocated anchor at that ride's queue."""
import json,math,os,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');SET=os.environ.get('CARNIVAL_RTP_SET','world')
OUT=ROOT/'Saved/WorldExpansion'/('ReturnToPathPIE_'+('' if SET=='world' else SET+'_')+'20261001');OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
SPOTS=[('under_mansion_causeway',(-64000,-84600,500)),('north_dock_water',(-49000,-57600,-150)),
 ('lab_b_gallery',(-43300,-5000,720)),('sewer_corridor',(-27050,-11100,-1700)),('atlantis_hall',(-13500,-11000,-1600)),
 ('prison_yard',(-28000,-30000,720)),('carnival_midway',(0,0,300)),('slums_street',(46000,72300,200)),('hospital_lobby',(97300,130100,760))]
EXPECT={}
if SET=='rides':
 SPOTS=[('circus_tent_inside',(-3827,3490,202)),('haunted_house_inside',(7707,4146,202)),
  ('flying_bobs_pit',(4848,-1774,202)),('swing_platform',(-6395,-2945,249))]
 EXPECT={'circus_tent_inside':'RouteAnchor_282','haunted_house_inside':'RouteAnchor_283','flying_bobs_pit':'RouteAnchor_281','swing_platform':'RouteAnchor_278'}
ANCHORS={}
V=unreal.Vector
R={'success':False,'errors':[],'spots':[],'limits':'Scripted calls in PIE; the pause-menu path is covered by native tests.'}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+400,'i':0}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'] and len(R['spots'])==len(SPOTS) and all(s.get('pass') for s in R['spots'])
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
  if S['phase']=='wait':
   # Live anchors in the game world (what ReturnToNearestRoute iterates), not the authoring report.
   for a in unreal.GameplayStatics.get_all_actors_with_tag(game,'CarnivalRouteAnchor'):ANCHORS[a.get_actor_label()]=a.get_actor_location().to_tuple()
   R['anchor_count']=len(ANCHORS)
   if not ANCHORS:return
   S.update(phase='place');return
  if S['phase']=='place':
   if S['i']>=len(SPOTS):finish();return
   name,loc=SPOTS[S['i']];p.get_movement_component().stop_movement_immediately()
   p.set_actor_location(V(*loc),False,True);S.update(phase='settle',until=now+1.5);return
  if S['phase']=='settle' and now>=S['until']:
   name,loc=SPOTS[S['i']];before=p.get_actor_location()
   ok=p.return_to_nearest_route();after=p.get_actor_location()
   lab,near=min(((k,math.dist(after.to_tuple(),a)) for k,a in ANCHORS.items()),key=lambda x:x[1])
   S.update(phase='hold',until=now+2.0,rec={'spot':name,'placed':loc,'before':list(before.to_tuple()),'returned':ok,'after':list(after.to_tuple()),'nearest_anchor':lab,'nearest_anchor_cm':round(near)});return
  if S['phase']=='hold' and now>=S['until']:
   r=S['rec'];end=p.get_actor_location();mv=p.get_movement_component()
   r.update(end=list(end.to_tuple()),drift_cm=round((end-V(*r['after'])).length()),walking=bool(mv.is_moving_on_ground()))
   r['pass']=bool(r['returned'] and r['nearest_anchor_cm']<250 and r['drift_cm']<60 and r['walking'] and EXPECT.get(r['spot'],r['nearest_anchor'])==r['nearest_anchor'])
   R['spots'].append(r);save();S.update(phase='place',i=S['i']+1)
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
