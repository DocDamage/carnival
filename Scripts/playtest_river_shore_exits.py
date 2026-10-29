"""PIE: the real player swims out of the river at a spread of the exits found by `audit_river_shore_exits.py`.

CARNIVAL_EXIT_SET=deep (the useful set): almost all of the river is 0-25 cm deep and only waded
(`probe_river_depth.py`), so instead start at the deepest point of each swimming-depth hole (>= 1.5 m) and swim to
the nearest audited bank exit (decks are tested on their own, from open water beside them), plus every deck exit. The default set below samples exits along the whole river.

Exits are picked by farthest-point sampling over the main river (so they cover its length), plus every deck exit and
one exit in each other pocket of 100+ m2. For each: start in swimming depth (bottom 1.5 m+ under the surface), found
by marching from the landing out across the shoreline sample for up to 40 m (decks: 5 m off, in the first direction
with open water); an exit with no swimming depth within 40 m is recorded as "shallow" (only ever waded). Start at the
surface; steer like a player (add_movement_input) toward the
exit landing. Pass = within 60 s the character stands on the landing (within 1.5 m), walking and out of the water
volume, having actually swum first. Many banks are shallows whose ground sits a little under the river surface level outside the swim boxes, so
"out" is the swim volume, not the surface height. After passing, it walks 3 s on toward a point 4 m inland and records
whether it stayed out ("inland": walked / back_in_water, e.g. a sandbar whose far side is water again). No saves.
"""
import json,math,os,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(r'F:\Carnival');AUDIT=ROOT/'Saved/WorldExpansion/RiverShoreExits_v3_20261001/index.json'
OUT=ROOT/'Saved/WorldExpansion'/('RiverShoreExitsPIE'+os.environ.get('CARNIVAL_AUDIT_SUFFIX','_20261001'));OUT.mkdir(parents=True,exist_ok=False)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);V=unreal.Vector
MAIN_PICKS=int(os.environ.get('CARNIVAL_EXIT_PICKS','16'));LIMIT_S=60.0;HALF=96.0
A=json.loads(AUDIT.read_text());SURF=A['surface_z'];G=A['grid']
comps=sorted(A['components'],key=lambda c:-c['samples']);main=comps[0]['id']
ex=A['exits']
def wpos(e):return (G['x0']+(e[0]+.5)*G['step'],G['y0']+(e[1]+.5)*G['step'])
picks=[];pool=[e for e in ex if e[5]==main and e[2]=='bank']
picks.append(min(pool,key=lambda e:e[3][0]))
while len(picks)<MAIN_PICKS:picks.append(max(pool,key=lambda e:min(math.dist(e[3][:2],p[3][:2]) for p in picks)))
picks+=[e for e in ex if e[2]=='deck']
for c in comps[1:]:
 if c['area_m2']>=100:
  cand=[e for e in ex if e[5]==c['id']]
  if cand:picks.append(cand[0])
TESTS=[]
if os.environ.get('CARNIVAL_EXIT_SET')=='deep':
 picks=[e for e in ex if e[2]=='deck']
 for c in json.loads((ROOT/'Saved/WorldExpansion/RiverDepth_20261001.json').read_text())['deep_clusters']:
  TESTS.append({'exit':['hole',None,'hole',None,None,None],'hole_bbox':c['bbox'],'start':None,'landing':None,'goal':None})
for e in picks:
 land=e[3];wx,wy=wpos(e);d=(land[0]-wx,land[1]-wy);n=math.hypot(*d) or 1.0;u=(d[0]/n,d[1]/n)
 if e[2]=='deck':TESTS.append({'exit':e,'start':None,'landing':land,'goal':None});continue
 TESTS.append({'exit':e,'start':(land[0]-u[0]*400,land[1]-u[1]*400,SURF-40),'landing':land,'goal':(land[0]+u[0]*400,land[1]+u[1]*400)})
R={'success':False,'errors':[],'surface_z':SURF,'tests':[]}
S={'phase':'wait','busy':False,'deadline':time.monotonic()+60+len(TESTS)*200,'i':0}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(err=None):
 if err:R['errors'].append(err)
 R['passed']=sum(1 for t in R['tests'] if t['pass']);R['count']=len(R['tests'])
 R['success']=not R['errors'] and R['count']==len(TESTS) and R['passed']==R['count']
 save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+5)
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if S['phase']=='exit':
   if now>S['deadline']:unreal.unregister_slate_post_tick_callback(h);unreal.SystemLibrary.quit_editor()
   return
  if now>S['deadline']:raise RuntimeError('wall-clock timeout in '+S['phase'])
  game=unreal.EditorLevelLibrary.get_game_world()
  if not game:return
  p=unreal.GameplayStatics.get_player_pawn(game,0)
  if not isinstance(p,unreal.CarnivalPlayerCharacter):return
  gt=unreal.GameplayStatics.get_time_seconds(game);mv=p.get_movement_component()
  if S['phase']=='wait':
   c=p.get_controller()
   if c:c.set_ignore_move_input(False)
   unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0');S.update(phase='place');return
  if S['phase']=='place':
   if S['i']>=len(TESTS):finish();return
   T=TESTS[S['i']];mv.stop_movement_immediately();p.set_swim_up_held(False);p.set_swim_down_held(False)
   def floor_z(x,y):
    h=unreal.SystemLibrary.line_trace_single(game,V(x,y,SURF+3000),V(x,y,SURF-3000),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True).to_tuple()
    return h[5].z if h[0] else None
   if 'hole_bbox' in T and T['start'] is None:
    # Deepest point of the hole (10 m grid), then the nearest audited exit landing.
    b=T['hole_bbox'];best=None
    for gx in range(int(b[0]),int(b[2])+1,1000):
     for gy in range(int(b[1]),int(b[3])+1,1000):
      z=floor_z(gx,gy)
      if z is not None and (best is None or z<best[2]):best=(gx,gy,z)
    # Up to three bank exits in clearly different directions (60+ degrees apart), nearest first: a player who
    # meets a bank they can't hold turns and tries another.
    bear=lambda e:math.degrees(math.atan2(e[3][1]-best[1],e[3][0]-best[0]))
    alts=[]
    for e in sorted((e for e in ex if e[2]=='bank'),key=lambda e:math.dist(e[3][:2],best[:2])):
     if all(abs((bear(e)-bear(a)+180)%360-180)>=60 for a in alts):alts.append(e)
     if len(alts)==3:break
    T.update(start=(best[0],best[1],SURF-40),hole_depth=round(SURF-best[2]),alts=alts,attempts=[])
   if 'alts' in T and T['landing'] is None:
    e=T['alts'][len(T['attempts'])];lx,ly=e[3][:2];d=(lx-T['start'][0],ly-T['start'][1]);n=math.hypot(*d) or 1.0
    T.update(exit=e,landing=e[3],goal=(lx+d[0]/n*400,ly+d[1]/n*400),deep=round(n))
   if T['exit'][2]=='bank' and 'deep' not in T:
    lx,ly=T['landing'][:2];ux,uy=(lx-T['start'][0])/400,(ly-T['start'][1])/400;T['deep']=None
    for k in range(2,81):
     z=floor_z(lx-ux*k*50,ly-uy*k*50)
     if z is not None and z<SURF-150:T['deep']=k*50+100;break
    if T['deep'] is None:
     R['tests'].append({'exit':T['exit'],'landing':T['landing'],'pass':True,'shallow':True,'note':'no swimming depth within 40 m: waded, never swum'});save();S['i']+=1;return
    T['start']=(lx-ux*T['deep'],ly-uy*T['deep'],SURF-40)
   if T['start'] is None:
    # Deck: start in open water 5 m off the deck; the goal is the deck itself plus 2 m.
    lx,ly=T['landing'][:2]
    for yaw in range(0,360,45):
     ux,uy=math.cos(math.radians(yaw)),math.sin(math.radians(yaw));sx,sy=lx+ux*500,ly+uy*500
     z=floor_z(sx,sy)
     if z is not None and z<SURF-150:T.update(start=(sx,sy,SURF-40),goal=(lx-ux*200,ly-uy*200));break
    if T['start'] is None:R['tests'].append({'exit':T['exit'],'landing':T['landing'],'pass':True,'shallow':True,'note':'no swimming depth within 5 m of the deck: waded, never swum'});save();S['i']+=1;return
   p.set_actor_location(V(*T['start']),False,True)
   S.update(phase='swim',t0=gt,rec={'exit':T['exit'],'start':[round(v) for v in T['start']],'landing':T['landing'],'start_from_landing_cm':T.get('deep',500),'failed_attempts':T.get('attempts',[]),'hole_depth_cm':T.get('hole_depth'),'samples':[]},last=-9.0,passed_landing=False,swam=False);return
  if S['phase']=='swim':
   T=TESTS[S['i']];r=S['rec'];pos=p.get_actor_location();feet=pos.z-HALF;inw=p.is_in_water_volume()
   walking=mv.is_moving_on_ground()
   if mv.is_swimming():S['swam']=True
   if 'out_at' not in S and S['swam'] and walking and not inw and (S['passed_landing'] or math.dist((pos.x,pos.y),T['landing'][:2])<=150):
    S['out_at']=gt;r.update({'pass':True,'seconds':round(gt-S['t0'],1),'out':[round(v) for v in pos.to_tuple()],'feet_minus_surface':round(feet-SURF)})
   if 'out_at' in S and inw:r['inland']='back_in_water'
   if 'out_at' in S and gt-S['out_at']>=3.0:
    r.setdefault('inland','walked');r['end']=[round(v) for v in pos.to_tuple()];del S['out_at']
    R['tests'].append(r);save();S.update(phase='place',i=S['i']+1);return
   if 'out_at' not in S and gt-S['t0']>LIMIT_S and 'alts' in T and len(T['attempts'])+1<len(T['alts']):
    T['attempts'].append({'exit':T['exit'],'end':[round(v) for v in pos.to_tuple()],'mode':str(mv.movement_mode)})
    T['landing']=None;S.update(phase='place');return
   if 'out_at' not in S and gt-S['t0']>LIMIT_S:
    r.update({'pass':False,'swam':S['swam'],'seconds':round(gt-S['t0'],1),'end':[round(v) for v in pos.to_tuple()],'mode':str(mv.movement_mode),'in_water':inw})
    R['tests'].append(r);save();S.update(phase='place',i=S['i']+1);return
   # Steer to the landing, then on inland to the goal.
   if math.dist((pos.x,pos.y),T['landing'][:2])<=120:S['passed_landing']=True
   tgt=T['goal'] if S['passed_landing'] else T['landing']
   d=(tgt[0]-pos.x,tgt[1]-pos.y);n=math.hypot(*d)
   if n>30:p.add_movement_input(V(d[0]/n,d[1]/n,0),1.0,True)
   if gt-S['last']>=1.0:
    r['samples'].append([round(gt-S['t0'],1)]+[round(v) for v in pos.to_tuple()]+[str(mv.movement_mode).split('.')[-1],inw]);S['last']=gt
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
try:
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for a in list(EA.get_all_level_actors()):
  if a.get_class().get_name()=='MetaHumanMassSpawner':EA.destroy_actor(a)
 R['planned']=len(TESTS);save()
 h=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
except Exception:
 R['errors'].append(traceback.format_exc());save();unreal.SystemLibrary.quit_editor()
