"""Read-only: where does the river show inside the dry override box (so it looks like water but can't be swum)?

5 m grid over the `Water_DryOverride_*` footprint: columns inside a river box whose first hit lies below the river
surface (visible water). Clusters with their bbox, floor range and floor actors; plus the bounds of the
underground structures the override protects (actors in the prison/sewer/tunnel levels inside the footprint),
reported as their top z per cluster bbox, to see how far the override's top could drop.
"""
import collections,json,math,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\DryOverrideWater_20261001.json')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE;STEP=500.0
R={'success':False,'errors':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ign=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 def box(a):
  o=a.get_actor_location();e=a.get_editor_property('water_extent');return (o.x-e.x,o.x+e.x,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z)
 dry=[box(a) for a in acts if a.get_actor_label().startswith('Water_DryOverride')];assert len(dry)==1;D=dry[0]
 river=[box(a) for a in acts if a.get_actor_label().startswith('Water_River_')];SURF=river[0][5]
 R.update(dry=[round(v) for v in D],surface=SURF)
 cells={}
 x=D[0]+STEP/2
 while x<D[1]:
  y=D[2]+STEP/2
  while y<D[3]:
   rb=[b for b in river if b[0]<=x<=b[1] and b[2]<=y<=b[3]]
   if rb:
    h=t(unreal.SystemLibrary.line_trace_single(w,V(x,y,3000),V(x,y,-6000),TQ,False,ign,N,True))
    if h and h[5].z<SURF-5:cells[(round(x),round(y))]=(round(h[5].z),h[9].get_actor_label() if h[9] else '',round(min(b[4] for b in rb)))
   y+=STEP
  x+=STEP
 R['visible_water_columns']=len(cells)
 seen=set();cl=[]
 for c in cells:
  if c in seen:continue
  q=[c];seen.add(c);m=[]
  while q:
   k=q.pop();m.append(k)
   for a in (-STEP,0,STEP):
    for b in (-STEP,0,STEP):
     n=(round(k[0]+a),round(k[1]+b))
     if n in cells and n not in seen:seen.add(n);q.append(n)
  bb=[min(p[0] for p in m),min(p[1] for p in m),max(p[0] for p in m),max(p[1] for p in m)]
  # Underground structures under this cluster (anything other than landscape, top below the surface).
  under=[]
  for a in acts:
   lv=a.get_level().get_outermost().get_name().split('/')[-1]
   if 'Landscape' in a.get_class().get_name() or a in ign:continue
   o,e=a.get_actor_bounds(False)
   if e.x>20000 or e.y>20000:continue
   if o.x+e.x<bb[0]-STEP or o.x-e.x>bb[2]+STEP or o.y+e.y<bb[1]-STEP or o.y-e.y>bb[3]+STEP:continue
   if o.z+e.z<SURF:under.append([round(o.z+e.z),a.get_actor_label(),lv])
  under.sort(reverse=True)
  cl.append({'columns':len(m),'bbox':bb,'floor_z':[min(cells[k][0] for k in m),max(cells[k][0] for k in m)],
   'floors':collections.Counter(cells[k][1] for k in m).most_common(3),'river_box_bottom':min(cells[k][2] for k in m),'highest_underground':under[:8]})
 R['clusters']=sorted(cl,key=lambda c:-c['columns'])
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
