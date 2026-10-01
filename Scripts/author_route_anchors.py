"""Author CarnivalRouteAnchor target points for the pause-menu "Return to path".

Anchor sources are positions the production character actually occupied in passing PIE walks
(2026-10-01), verified campaign station stands, and the Carnival ride queue points. Each candidate
gets a fresh walkable-floor and standing-capsule check; candidates within 15 m of an accepted
anchor are merged. Anchors go in the always-loaded connectors level, which is the only level saved
(backed up first).
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_CarnivalWorldExpansion_Connections_Layout'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/RouteAnchors_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
TAG='CarnivalRouteAnchor';SPACING=1500.0
R={'success':False,'errors':[],'sources':{},'rejected':0,'anchors':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def load(rel):return json.loads((ROOT/rel).read_text())
try:
 cands=[]
 def add(src,points):
  R['sources'][src]=R['sources'].get(src,0)+len(points);cands.extend((src,p) for p in points)
 for rel in ('Saved/WorldExpansion/AfterPrisonBlockers_Walk_20261001.json','Saved/WorldExpansion/OuterSpine_After_PropResite_20261001.json'):
  for test in load(rel)['tests']:add(rel.split('/')[-1],[s['position_cm'] for s in test.get('samples',[])])
 for test in load('Saved/IndustrialHospital/Route_Playtest_After_PropResite_20261001.json')['tests']:
  if test['name'].startswith('walk'):add('HospitalRoad_walk',[s['position'] for s in test.get('samples',[])])
 for test in load('Saved/MansionConnection/Route_Playtest.json')['tests']:
  if test.get('mode')=='walk':add('MansionRoute_walk',[s['position'] for s in test.get('samples',[])])
 stands=[]
 for name in ('CampaignStationsAuthored2_20260930','CampaignStationsAuthored3_20260930','CampaignStationsAuthored4_20260930','CampaignStationsAuthored5_20261001'):
  for row in load('Saved/CampaignAcceptance/'+name+'/index.json')['placed']:
   stands+=[a['stand'] for a in row['actors']]
 for h in load('Saved/CampaignAcceptance/HospitalStationsAuthoredDeskTop_20260930/index.json')['stations']:stands.append(h['approach'])
 add('station_stands',stands)
 R['map_sha256_before']=sha(MAPFILE);R['level_sha256_before']=sha(LEVEL_FILE)
 shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_route_anchors.umap'))
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 acts=EA.get_all_level_actors()
 assert not any(TAG in [str(x) for x in a.tags] for a in acts),'Anchors already authored'
 add('carnival_queue_points',[list(a.get_actor_location().to_tuple()) for a in acts if a.get_actor_label().startswith('CarnivalQueuePoint_')])
 assert LE.set_current_level_by_name(LEVEL)
 accepted=[]
 for src,p in cands:
  x,y,z=p
  if any(math.dist((x,y,z),(a[0],a[1],a[2]))<SPACING for a in accepted):continue
  f=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,z+80),V(x,y,z-300),TQ,False,[],N,True))
  if not f or f[7].z<.707:R['rejected']+=1;continue
  c=f[5]+V(0,0,98)
  if t(unreal.SystemLibrary.capsule_trace_single(world,c,c+V(0,0,.1),42,96,TQ,False,[],N,True)):R['rejected']+=1;continue
  a=EA.spawn_actor_from_class(unreal.TargetPoint,c,unreal.Rotator(roll=0.0,pitch=0.0,yaw=0.0))
  a.tags=[unreal.Name(TAG)];a.set_actor_label('RouteAnchor_%03d'%len(accepted));a.set_folder_path('RouteAnchors')
  assert '/'+LEVEL+'.' in a.get_path_name()
  accepted.append(list(c.to_tuple()));R['anchors'].append({'label':a.get_actor_label(),'location':accepted[-1],'source':src,'floor':f[9].get_actor_label() if f[9] else ''})
 assert accepted
 anchor0=next(x for x in EA.get_all_level_actors() if x.get_actor_label()=='RouteAnchor_000')
 assert unreal.EditorLoadingAndSavingUtils.save_packages([anchor0.get_outermost()],False)
 R.update(map_sha256_after=sha(MAPFILE),level_sha256_after=sha(LEVEL_FILE));assert R['map_sha256_after']==R['map_sha256_before']
 R['count']=len(accepted);R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
