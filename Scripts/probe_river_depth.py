"""Read-only: how deep is the swimmable river? 10 m grid over the `Water_River_*` boxes (minus the dry override):
first hit below the surface -> depth. Histogram, and the deep (swimming-depth, >= 1.5 m) areas as clusters."""
import collections,json,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\RiverDepth_20261001.json')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE;STEP=1000.0
R={'success':False,'errors':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ign=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 def box(a):
  o=a.get_actor_location();e=a.get_editor_property('water_extent');return (o.x-e.x,o.x+e.x,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z)
 river=[box(a) for a in acts if a.get_actor_label().startswith('Water_River_')]
 dry=[box(a) for a in acts if a.get_actor_label().startswith('Water_DryOverride')]
 SURF=river[0][5];hist=collections.Counter();deep={};seen=set()
 for b in river:
  x=b[0]+STEP/2
  while x<b[1]:
   y=b[2]+STEP/2
   while y<b[3]:
    k=(round(x),round(y))
    if k not in seen and not any(d[0]<=x<=d[1] and d[2]<=y<=d[3] for d in dry):
     seen.add(k);h=t(unreal.SystemLibrary.line_trace_single(w,V(x,y,SURF+3000),V(x,y,b[4]-500),TQ,False,ign,N,True))
     if h and h[5].z<SURF:
      dep=SURF-h[5].z;hist[min(int(dep//25)*25,500)]+=1
      if dep>=150:deep[k]=[round(dep),h[9].get_actor_label() if h[9] else '']
    y+=STEP
   x+=STEP
 R['surface']=SURF;R['wet_samples_10m']=sum(hist.values());R['depth_histogram_cm']=dict(sorted(hist.items()))
 cl=[];done=set()
 for k in deep:
  if k in done:continue
  q=[k];done.add(k);m=[]
  while q:
   c=q.pop();m.append(c)
   for a in (-STEP,0,STEP):
    for b2 in (-STEP,0,STEP):
     n=(round(c[0]+a),round(c[1]+b2))
     if n in deep and n not in done:done.add(n);q.append(n)
  cl.append({'samples':len(m),'area_m2':len(m)*100,'bbox':[min(p[0] for p in m),min(p[1] for p in m),max(p[0] for p in m),max(p[1] for p in m)],
   'max_depth':max(deep[p][0] for p in m),'floors':collections.Counter(deep[p][1] for p in m).most_common(3)})
 R['deep_clusters']=sorted(cl,key=lambda c:-c['samples'])
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
