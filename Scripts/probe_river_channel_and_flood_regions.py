"""Read-only: (1) river channel cross-sections along the WaterBodyRiver spline - where the landscape lies below the
-240 water surface (ignoring the editor-only far-landscape mesh); (2) bounds of the Atlantis, Shipwreck and Sewer
levels and of the R11/R12 tunnel pieces, for sizing water volumes. No saves."""
import json,math,traceback
from collections import defaultdict
import unreal
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
OUT=r'F:\Carnival\Saved\WorldExpansion\RiverChannelFloodRegions_20261001.json'
R={'errors':[],'sections':[],'levels':{},'tunnel_actors':[]}
SURF=-240.0
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 far=[a for a in acts if 'Landscape_Far' in a.get_actor_label()]
 river=next(a for a in acts if a.get_actor_label()=='WaterBodyRiver')
 sp=river.get_component_by_class(unreal.SplineComponent);L=sp.get_spline_length()
 def ground(x,y):
  h=unreal.SystemLibrary.line_trace_single(w,V(x,y,4000),V(x,y,-4000),TQ,True,far+[river],N,True)
  t=h.to_tuple() if h else None
  return (t[5].z,t[9].get_actor_label() if t[9] else '?') if t and t[0] else (None,None)
 d=0.0
 while d<=L:
  p=sp.get_location_at_distance_along_spline(d,unreal.SplineCoordinateSpace.WORLD)
  tg=sp.get_tangent_at_distance_along_spline(d,unreal.SplineCoordinateSpace.WORLD);tg.z=0;tg=tg.normal()
  nx,ny=-tg.y,tg.x
  wet=[]
  for o in range(-80000,80001,1000):
   z,lab=ground(p.x+nx*o,p.y+ny*o)
   if z is not None and z<SURF-5:wet.append(o)
  # contiguous wet run containing / nearest the centreline
  runs=[];cur=None
  for o in wet:
   if cur and o-cur[1]<=1000:cur[1]=o
   else:
    cur=[o,o];runs.append(cur)
  R['sections'].append({'d_m':round(d/100),'centre':[round(p.x),round(p.y)],'normal':[round(nx,3),round(ny,3)],'runs':runs})
  d+=5000
 by=defaultdict(list)
 for a in acts:
  lv=a.get_level().get_outermost().get_name().split('/')[-1]
  if any(k in lv for k in ('Atlantis','Shipwreck','Sewers')):
   if a.get_class().get_name() in ('StaticMeshActor','SkeletalMeshActor','CarnivalMissionInteractionActor'):
    o,e=a.get_actor_bounds(False);by[lv].append((o-e,o+e))
  lab=a.get_actor_label()
  if 'Connections' in lv and any(k in lab for k in ('Atlantis','Sewer','Shipwreck','R11','R12','Tunnel')):
   o,e=a.get_actor_bounds(False);R['tunnel_actors'].append({'label':lab,'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()],'yaw':round(a.get_actor_rotation().yaw,1)})
 for lv,bs in by.items():
  lo=[min(b[0].x for b in bs),min(b[0].y for b in bs),min(b[0].z for b in bs)];hi=[max(b[1].x for b in bs),max(b[1].y for b in bs),max(b[1].z for b in bs)]
  R['levels'][lv]={'min':[round(v) for v in lo],'max':[round(v) for v in hi],'count':len(bs)}
except Exception:R['errors'].append(traceback.format_exc())
open(OUT,'w').write(json.dumps(R,indent=1))
