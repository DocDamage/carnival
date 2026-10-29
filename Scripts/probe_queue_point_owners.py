"""Read-only: which CarnivalQueuePoint sets have an owning CarnivalRideQueueComponent (matching RideId).

Lists every queue component's RideId (with its actor and level) and every queue point grouped by RideId,
and which route anchors (RouteAnchor_*) sit within 50 cm of a queue point.
"""
import json,math,traceback
from collections import defaultdict
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\QueuePointOwners_20261001.json')
R={'success':False,'errors':[]}
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 comps=[];points=defaultdict(list);anchors=[]
 for a in acts:
  lvl=a.get_level().get_outermost().get_name().split('/')[-1]
  for c in a.get_components_by_class(unreal.CarnivalRideQueueComponent):
   comps.append([str(c.get_editor_property('ride_id')),a.get_actor_label(),lvl])
  if isinstance(a,unreal.CarnivalQueuePoint):
   points[str(a.get_editor_property('ride_id'))].append([a.get_actor_label(),lvl]+[round(v) for v in a.get_actor_location().to_tuple()])
  if a.get_actor_label().startswith('RouteAnchor_'):anchors.append([a.get_actor_label()]+list(a.get_actor_location().to_tuple()))
 owned={c[0] for c in comps}
 R['components']=sorted(comps)
 R['point_sets']={k:{'count':len(v),'owned':(k in owned) or ('None' in owned),'levels':sorted({p[1] for p in v}),'first':v[0][0]} for k,v in sorted(points.items())}
 R['orphan_points']=sorted(p[0] for k,v in points.items() if k not in owned and 'None' not in owned for p in v)
 R['anchors_on_orphans']=sorted({an[0] for an in anchors for k,v in points.items() if k not in owned for p in v if math.dist(an[1:3],p[2:4])<50})
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
