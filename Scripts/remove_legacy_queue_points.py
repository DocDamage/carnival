"""Remove the orphaned legacy ride queue lines and the two route anchors placed inside ride buildings.

`place_queue_points.py` once put 8 `CarnivalQueuePoint_<Ride>_NN` markers in a straight line from nine ride
origins with plain RideIds ("Circus", ...). The attended rides later moved to per-instance RideIds with their
own `AttendedQueue_*` / `BalloonStation_*_Queue_*` markers, so no `CarnivalRideQueueComponent` claims the old
lines (`Saved/WorldExpansion/QueuePointOwners_20261001.json`). The Circus and Haunted House lines start inside
their buildings, and `author_route_anchors.py` turned them into route anchors 282 (inside the closed circus tent)
and 283 (inside the haunted house). "Return to path" teleports to the nearest anchor, so near those rides it put
the player somewhere with no way out.

This deletes every queue point whose RideId has no owning component (asserting all 72 are the legacy lines) from
LV_Carnival, and RouteAnchor_282/283 from the connectors level. Both packages are backed up first.
"""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
OUT=ROOT/'Saved/WorldExpansion/RemoveLegacyQueuePoints_20261001';OUT.mkdir(parents=True,exist_ok=False)
BAD_ANCHORS=('RouteAnchor_282','RouteAnchor_283')
R={'success':False,'errors':[],'removed_points':[],'removed_anchors':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 R.update(map_sha256_before=sha(MAPFILE),level_sha256_before=sha(LEVEL_FILE))
 shutil.copy2(MAPFILE,OUT/'LV_Carnival.before_legacy_queue_removal.umap')
 shutil.copy2(LEVEL_FILE,OUT/'L_CarnivalWorldExpansion_Connections_Layout.before_legacy_queue_removal.umap')
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);acts=EA.get_all_level_actors()
 owned={str(c.get_editor_property('ride_id')) for a in acts for c in a.get_components_by_class(unreal.CarnivalRideQueueComponent)}
 assert 'None' not in owned and '' not in owned,'A queue component with no RideId would claim every point'
 orphans=[a for a in acts if isinstance(a,unreal.CarnivalQueuePoint) and str(a.get_editor_property('ride_id')) not in owned]
 assert len(orphans)==72 and all(a.get_actor_label().startswith('CarnivalQueuePoint_') for a in orphans),[a.get_actor_label() for a in orphans]
 assert all(a.get_level().get_outermost().get_name().endswith('/LV_Carnival') for a in orphans)
 anchors=[a for a in acts if a.get_actor_label() in BAD_ANCHORS]
 assert len(anchors)==2 and all('CarnivalRouteAnchor' in [str(t) for t in a.tags] for a in anchors)
 assert all('/L_CarnivalWorldExpansion_Connections_Layout.' in a.get_path_name() for a in anchors)
 pkgs=[orphans[0].get_outermost(),anchors[0].get_outermost()]
 for a in orphans+anchors:
  (R['removed_points'] if a in orphans else R['removed_anchors']).append([a.get_actor_label()]+[round(v) for v in a.get_actor_location().to_tuple()])
  assert EA.destroy_actor(a)
 assert unreal.EditorLoadingAndSavingUtils.save_packages(pkgs,False)
 R.update(map_sha256_after=sha(MAPFILE),level_sha256_after=sha(LEVEL_FILE))
 assert R['map_sha256_after']!=R['map_sha256_before'] and R['level_sha256_after']!=R['level_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
