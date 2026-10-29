"""Move the route anchors that came from the legacy queue lines inside rides onto the rides' real queue heads.

`author_route_anchors.py` built anchors 278/281/282/283 from the legacy `CarnivalQueuePoint_*` lines
(removed by `remove_legacy_queue_points.py`). 282/283 (inside the circus tent and the haunted house) are already
deleted. 278 stands on the swing ride's platform under its seats, and 281 is in the pit under the Flying Bobs deck
(`Saved/WorldExpansion/AnchorEnclosure_20261001.json`). "Return to path" teleports to the nearest anchor, so each
ride gets its anchor back at queue index 0 of its owned attended queue (the attendant side, open ground), after
the same floor and standing-capsule checks `author_route_anchors.py` uses. Only the connectors level is saved.
"""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_CarnivalWorldExpansion_Connections_Layout'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/RelocateRideRouteAnchors_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE;TAG='CarnivalRouteAnchor'
# anchor label -> queue head label prefix (index 0 of the ride's owned queue)
MOVES={'RouteAnchor_278':'AttendedQueue_Swing_','RouteAnchor_281':'AttendedQueue_FlyingBobs_',
       'RouteAnchor_282':'AttendedQueue_Circus_','RouteAnchor_283':'AttendedQueue_HauntedHouse_'}
R={'success':False,'errors':[],'moves':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 R.update(map_sha256_before=sha(MAPFILE),level_sha256_before=sha(LEVEL_FILE))
 shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_anchor_relocation.umap'))
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 acts=EA.get_all_level_actors();by={a.get_actor_label():a for a in acts}
 assert 'RouteAnchor_282' not in by and 'RouteAnchor_283' not in by,'Run remove_legacy_queue_points.py first'
 assert LE.set_current_level_by_name(LEVEL)
 for label,prefix in MOVES.items():
  heads=[a for a in acts if isinstance(a,unreal.CarnivalQueuePoint) and a.get_actor_label().startswith(prefix) and a.get_editor_property('queue_index')==0]
  assert len(heads)==1,(label,[h.get_actor_label() for h in heads])
  q=heads[0].get_actor_location()
  f=t(unreal.SystemLibrary.line_trace_single(w,q+V(0,0,80),q-V(0,0,300),TQ,False,[],N,True))
  assert f and f[7].z>=.707,(label,'no walkable floor')
  c=f[5]+V(0,0,98)
  blocked=t(unreal.SystemLibrary.capsule_trace_single(w,c,c+V(0,0,.1),42,96,TQ,False,[],N,True))
  assert not blocked,(label,blocked[9].get_actor_label() if blocked[9] else '?')
  row={'label':label,'queue_head':heads[0].get_actor_label(),'floor':f[9].get_actor_label() if f[9] else '','new':[round(v) for v in c.to_tuple()]}
  old=by.get(label)
  if old:
   assert TAG in [str(x) for x in old.tags] and '/'+LEVEL+'.' in old.get_path_name()
   row['old']=[round(v) for v in old.get_actor_location().to_tuple()];old.set_actor_location(c,False,False)
  else:
   a=EA.spawn_actor_from_class(unreal.TargetPoint,c,unreal.Rotator(roll=0.0,pitch=0.0,yaw=0.0))
   a.tags=[unreal.Name(TAG)];a.set_actor_label(label);a.set_folder_path('RouteAnchors')
   assert '/'+LEVEL+'.' in a.get_path_name();row['old']=None
  R['moves'].append(row)
 a0=next(x for x in EA.get_all_level_actors() if x.get_actor_label()=='RouteAnchor_000')
 assert unreal.EditorLoadingAndSavingUtils.save_packages([a0.get_outermost()],False)
 R.update(map_sha256_after=sha(MAPFILE),level_sha256_after=sha(LEVEL_FILE));assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
