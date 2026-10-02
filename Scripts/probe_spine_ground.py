"""Read-only: what lies under the OuterRoute spine and the dock decks? For every `OuterRoute_Segment` (and every
East/North Dock deck slab), trace down from just under the deck, at its centre and both side edges: the first
non-deck surface below (ignoring the editor-only far terrain). A segment with nothing below within 60 m is over the
void, where stepping off its edge is an endless fall. Grouped into runs along the spine."""
import json,math,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\SpineGround_20261001.json')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
R={'success':False,'errors':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ign=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 segs=[a for a in acts if a.get_actor_label().startswith('OuterRoute_Segment')]
 decks=[a for a in acts if a.get_actor_label().startswith(('EastDock_','NorthDock_','DockNorth_')) and a.get_component_by_class(unreal.StaticMeshComponent)]
 rows=[]
 for a in segs+decks:
  o,e=a.get_actor_bounds(False);r=a.get_actor_right_vector();f=a.get_actor_forward_vector()
  side=max(e.x,e.y)  # bounds are axis aligned; use the smaller horizontal half-width for the edge offset
  half=min(abs(r.x)*e.x+abs(r.y)*e.y, max(e.x,e.y))
  res=[]
  for off in (0,-half-60,half+60):
   p=V(o.x+r.x*off,o.y+r.y*off,o.z-e.z-5)
   h=t(unreal.SystemLibrary.line_trace_single(w,p,p-V(0,0,6000),TQ,False,ign+[a],N,True))
   res.append([round(o.z+e.z-h[5].z),h[9].get_actor_label() if h[9] else ''] if h else None)
  rows.append({'label':a.get_actor_label(),'level':a.get_level().get_outermost().get_name().split('/')[-1],'center':[round(v) for v in o.to_tuple()],
   'top':round(o.z+e.z),'below':res,'void':all(x is None for x in res),'edge_void':res[1] is None or res[2] is None})
 R['segments']=len(segs);R['decks']=len(decks)
 R['void_segments']=sum(1 for x in rows if x['void'] and x['label'].startswith('OuterRoute'))
 R['edge_void_segments']=sum(1 for x in rows if x['edge_void'] and x['label'].startswith('OuterRoute'))
 R['void_decks']=[x['label'] for x in rows if x['edge_void'] and not x['label'].startswith('OuterRoute')]
 # runs of consecutive (by position along the chain) void spine segments
 sp=[x for x in rows if x['label'].startswith('OuterRoute')]
 def idx(l):
  try:return int(''.join(c for c in l.split('_')[-1] if c.isdigit()) or 0)
  except:return 0
 sp.sort(key=lambda x:idx(x['label']))
 runs=[];cur=None
 for x in sp:
  if x['edge_void']:
   if cur and idx(x['label'])==cur['last']+1:cur['last']=idx(x['label']);cur['n']+=1;cur['end']=x['center']
   else:cur={'first':idx(x['label']),'last':idx(x['label']),'n':1,'start':x['center'],'end':x['center']};runs.append(cur)
  else:cur=None
 R['edge_void_runs']=runs;R['rows']=rows
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
