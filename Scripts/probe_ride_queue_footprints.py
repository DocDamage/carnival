"""Read-only: why the Circus and Haunted House queue lines are unreachable, and where they could go.

For each ride: actor transform and bounds, its queue points, and a radial scan from the ride origin at
waist height (first Visibility hit per 5 degree yaw, i.e. the building walls and any open entrance).
Then standable floor candidates on rings outside the footprint, each with a standing-capsule check and a
straight Visibility trace back toward the ride origin (to find the side that faces the entrance).
"""
import json,math,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\RideQueueFootprints_20261001.json')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
RIDES={'Circus':'BP_Circus_Carnival','HauntedHouse':'BP_HauntedHouse_Carnival'}
R={'success':False,'errors':[],'rides':{}}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def lbl(a):return a.get_actor_label() if a else ''
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 def floor(x,y,ztop,zbot):
  f=t(unreal.SystemLibrary.line_trace_single(w,V(x,y,ztop),V(x,y,zbot),TQ,False,[],N,True))
  return f
 for rid,label in RIDES.items():
  ride=next(a for a in acts if lbl(a)==label)
  o=ride.get_actor_location();fw=ride.get_actor_forward_vector();bo,be=ride.get_actor_bounds(False)
  e={'location':list(o.to_tuple()),'yaw':ride.get_actor_rotation().yaw,'forward':list(fw.to_tuple()),
     'bounds_origin':list(bo.to_tuple()),'bounds_extent':list(be.to_tuple()),'queue_points':[],'radial':[],'ring':[]}
  for a in acts:
   if lbl(a).startswith('CarnivalQueuePoint_'+rid+'_'):e['queue_points'].append([lbl(a)]+[round(v) for v in a.get_actor_location().to_tuple()])
  e['queue_points'].sort()
  f0=floor(o.x,o.y,o.z+400,o.z-600);gz=f0[5].z if f0 else o.z
  e['floor_at_origin']=[lbl(f0[9]) if f0 else None,round(gz)]
  for yaw in range(0,360,5):
   d=V(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)),0)
   s=V(o.x,o.y,gz+90);h=t(unreal.SystemLibrary.line_trace_single(w,s,s+d*4000,TQ,False,[],N,True))
   e['radial'].append([yaw,round(h[3]) if h else None,lbl(h[9]) if h else None,h[10].get_name() if h and h[10] else None])
  rad=max(be.x,be.y)
  for ring in (rad+150,rad+400):
   for yaw in range(0,360,15):
    d=V(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)),0);p=V(bo.x,bo.y,0)+d*ring
    f=floor(p.x,p.y,o.z+500,o.z-400)
    if not f:e['ring'].append([round(ring),yaw,None]);continue
    c=f[5]+V(0,0,98)
    blocked=t(unreal.SystemLibrary.capsule_trace_single(w,c,c+V(0,0,.1),42,96,TQ,False,[],N,True))
    back=t(unreal.SystemLibrary.line_trace_single(w,c,V(o.x,o.y,c.z),TQ,False,[],N,True))
    e['ring'].append([round(ring),yaw,[round(v) for v in f[5].to_tuple()],lbl(f[9]),round(f[7].z,2),lbl(blocked[9]) if blocked else None,
                      [round(back[3]),lbl(back[9])] if back else None])
  e['attendants']=[[lbl(a)]+[round(v) for v in a.get_actor_location().to_tuple()]+[round(a.get_actor_rotation().yaw)] for a in acts if rid.lower() in lbl(a).lower() and 'attendant' in lbl(a).lower()]
  e['nearby']=sorted([[round(math.dist((o.x,o.y),(a.get_actor_location().x,a.get_actor_location().y))),lbl(a),a.get_class().get_name()]+[round(v) for v in a.get_actor_location().to_tuple()] for a in acts if a!=ride and math.dist((o.x,o.y),(a.get_actor_location().x,a.get_actor_location().y))<rad+900 and any(k in lbl(a).lower() for k in ('ticket','sign','entr','door','gate','attend','ride','stair','ramp'))])[:40]
  R['rides'][rid]=e
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
