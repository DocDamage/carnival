"""Read-only: is a route anchor enclosed? Standing-capsule check at the anchor, then waist-height Visibility rays
every 15 degrees (distance to first hit), and whether a standing capsule fits 2 m and 4 m out along each ray."""
import json,math,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\AnchorEnclosure_20261001.json')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
LABELS=('RouteAnchor_278','RouteAnchor_281')
R={'success':False,'errors':[],'anchors':{}}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def lbl(h):return h[9].get_actor_label() if h and h[9] else None
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 for name in LABELS:
  a=next(x for x in acts if x.get_actor_label()==name);c=a.get_actor_location()
  f=t(unreal.SystemLibrary.line_trace_single(w,c,c-V(0,0,300),TQ,False,[],N,True))
  e={'location':[round(v) for v in c.to_tuple()],'floor':[lbl(f),round(f[5].z)] if f else None,
     'capsule_block':lbl(t(unreal.SystemLibrary.capsule_trace_single(w,c,c+V(0,0,.1),42,96,TQ,False,[],N,True))),'rays':[]}
  for yaw in range(0,360,15):
   d=V(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)),0);s=c-V(0,0,10)
   h=t(unreal.SystemLibrary.line_trace_single(w,s,s+d*600,TQ,False,[],N,True))
   fits=[]
   for r in (200,400):
    p=c+d*r;g=t(unreal.SystemLibrary.line_trace_single(w,p+V(0,0,200),p-V(0,0,400),TQ,False,[],N,True))
    if not g:fits.append(None);continue
    q=g[5]+V(0,0,98);fits.append([lbl(g),round(g[5].z),lbl(t(unreal.SystemLibrary.capsule_trace_single(w,q,q+V(0,0,.1),42,96,TQ,False,[],N,True)))])
   e['rays'].append([yaw,round(h[3]) if h else None,lbl(h),fits])
  R['anchors'][name]=e
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
