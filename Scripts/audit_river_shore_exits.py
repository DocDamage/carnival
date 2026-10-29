"""Read-only: can a swimmer get out of the river everywhere they can get in?

Samples the `Water_River_*` boxes (minus `Water_DryOverride_*`) on a 5 m grid. A sample is water when the column
under the surface is open (open water, or water under a deck). Each water sample beside a non-water sample is
shoreline; from it the audit marches toward the bank in 25 cm steps and applies the character's own climb-out
test (`ACarnivalPlayerCharacter`, swim tick): a walkable hit on a trace from surface+160 down to surface-30, with a
standing capsule clear above it. Walkable slopes that rise out of the water (wade-outs) pass the same test where
they cross the surface. A deck whose walkable top is within 160 cm of the surface is an exit from under its edge.

Water samples are grouped (8-connected), and for every shoreline sample the swim distance through water to the
nearest exit is measured. Shore stretches with no exit within EXIT_SWIM_M are reported as clusters.
Limits: Visibility traces for both tests (the game uses Pawn for the capsule); exits are not yet checked for
connection to the walk network, so an exit onto an islet still counts; the editor-only far terrain is ignored.
"""
import collections,json,math,os,time,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion')/('RiverShoreExits'+os.environ.get('CARNIVAL_AUDIT_SUFFIX','_20261001'));OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
STEP=500.0;EXIT_SWIM_M=60.0;WALKABLE_Z=0.71;CAP_R=42.0;CAP_HH=96.0
R={'success':False,'errors':[],'limits':__doc__.split('Limits:')[1].strip()}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def name(h):return h[9].get_actor_label() if h and h[9] else ''
try:
 t0=time.time()
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ignore=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 def box(a):
  o=a.get_actor_location();e=a.get_editor_property('water_extent');r=a.get_actor_rotation()
  assert abs(r.yaw)%90<1 or abs(r.yaw)%90>89,(a.get_actor_label(),r.yaw)
  if abs(round(r.yaw/90))%2:e=V(e.y,e.x,e.z)
  return (o.x-e.x,o.x+e.x,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z)
 water=[a for a in acts if isinstance(a,unreal.CarnivalWaterVolume)]
 river=[box(a) for a in water if a.get_actor_label().startswith('Water_River_')]
 dry=[box(a) for a in acts if a.get_actor_label().startswith('Water_DryOverride')]
 assert river,'no river boxes'
 SURF=river[0][5];assert all(abs(b[5]-SURF)<1 for b in river),'river surfaces differ'
 R.update(river_boxes=len(river),dry_boxes=len(dry),surface_z=SURF)
 def in_river(x,y):return any(b[0]<=x<=b[1] and b[2]<=y<=b[3] for b in river)
 def in_dry(x,y):return any(b[0]<=x<=b[1] and b[2]<=y<=b[3] and b[4]<=SURF-50<=b[5] for b in dry)
 def line(a,b):return t(unreal.SystemLibrary.line_trace_single(w,a,b,TQ,False,ignore,N,True))
 def capsule_clear(p):return not t(unreal.SystemLibrary.capsule_trace_single(w,p,p+V(0,0,.1),CAP_R,CAP_HH,TQ,False,ignore,N,True))
 def ledge(x,y):
  h=line(V(x,y,SURF+160),V(x,y,SURF-30))
  if not h or h[7].z<WALKABLE_Z:return None
  return (h[5].z,name(h)) if capsule_clear(h[5]+V(0,0,CAP_HH+5)) else None
 # 1) classify samples
 xs=[b[0] for b in river]+[b[1] for b in river];ys=[b[2] for b in river]+[b[3] for b in river]
 x0,y0=min(xs),min(ys);ix_n=int((max(xs)-x0)/STEP)+1;iy_n=int((max(ys)-y0)/STEP)+1
 pos=lambda i,j:(x0+(i+.5)*STEP,y0+(j+.5)*STEP)
 R['grid']={'x0':x0,'y0':y0,'step':STEP}
 wet={};phantom=0
 for i in range(ix_n):
  for j in range(iy_n):
   x,y=pos(i,j)
   if not in_river(x,y) or in_dry(x,y):continue
   top=line(V(x,y,SURF+3000),V(x,y,SURF-3000))
   if top and top[5].z<SURF-5:wet[(i,j)]=('open',round(top[5].z));continue
   # Water under a deck: a low deck over a bottom inside this river box (not, e.g., a flooded interior far below).
   bot=min(b[4] for b in river if b[0]<=x<=b[1] and b[2]<=y<=b[3])
   under=line(V(x,y,SURF-5),V(x,y,bot))
   if top and under and top[5].z<=SURF+600 and name(top)!=name(under):wet[(i,j)]=('covered',round(top[5].z),name(top))
 R['wet_samples']=len(wet);R['classify_seconds']=round(time.time()-t0)
 # 2) shoreline and exits
 NB=[(a,b) for a in (-1,0,1) for b in (-1,0,1) if a or b]
 exits={};shore=set()
 for (i,j),info in wet.items():
  x,y=pos(i,j)
  if info[0]=='covered' and info[1]<=SURF+160:
   l=ledge(x,y)
   if l:exits[(i,j)]=['deck',[round(x),round(y),round(l[0])],l[1]];continue
  dry_nb=[(i+a,j+b) for a,b in NB if (i+a,j+b) not in wet]
  if not dry_nb:continue
  shore.add((i,j))
  for (p,q) in dry_nb:
   tx,ty=pos(p,q);d=math.dist((x,y),(tx,ty));found=None
   for k in range(1,int(d/25)+1):
    f=k*25/d;l=ledge(x+(tx-x)*f,y+(ty-y)*f)
    if l:found=['bank',[round(x+(tx-x)*f),round(y+(ty-y)*f),round(l[0])],l[1]];break
   if found:exits[(i,j)]=found;break
 shore|=set(exits)
 R['shore_samples']=len(shore);R['exit_samples']=len(exits)
 # 3) components and swim distance to the nearest exit
 comp={};comps=[]
 for s in wet:
  if s in comp:continue
  cid=len(comps);comp[s]=cid;q=[s];members=[]
  while q:
   c=q.pop();members.append(c)
   for a,b in NB:
    n=(c[0]+a,c[1]+b)
    if n in wet and n not in comp:comp[n]=cid;q.append(n)
  comps.append(members)
 dist={e:0.0 for e in exits};pq=collections.deque(exits)
 # BFS on grid hops (diagonals count as one hop); hop length is STEP to keep it simple and conservative-ish
 while pq:
  c=pq.popleft()
  for a,b in NB:
   n=(c[0]+a,c[1]+b)
   if n in wet and n not in dist:dist[n]=dist[c]+STEP*(1.414 if a and b else 1);pq.append(n)
 R['components']=[]
 for cid,members in enumerate(comps):
  sh=[m for m in members if m in shore];ex=[m for m in members if m in exits]
  far=[m for m in sh if dist.get(m,1e12)>EXIT_SWIM_M*100]
  xs_=[pos(*m)[0] for m in members];ys_=[pos(*m)[1] for m in members]
  R['components'].append({'id':cid,'samples':len(members),'area_m2':round(len(members)*(STEP/100)**2),'bbox':[round(min(xs_)),round(min(ys_)),round(max(xs_)),round(max(ys_))],
   'shore':len(sh),'exits':len(ex),'max_swim_to_exit_m':round(max([dist.get(m,1e12) for m in sh] or [0])/100,1) if ex else None,'shore_beyond_limit':len(far)})
 # clusters of shoreline with no exit within the limit
 far=set(m for m in shore if dist.get(m,1e12)>EXIT_SWIM_M*100);clusters=[];seen=set()
 for s in far:
  if s in seen:continue
  q=[s];seen.add(s);mem=[]
  while q:
   c=q.pop();mem.append(c)
   for a in range(-2,3):
    for b in range(-2,3):
     n=(c[0]+a,c[1]+b)
     if n in far and n not in seen:seen.add(n);q.append(n)
  ps=[pos(*m) for m in mem];worst=max(mem,key=lambda m:dist.get(m,1e12))
  clusters.append({'shore_samples':len(mem),'centroid':[round(sum(p[0] for p in ps)/len(ps)),round(sum(p[1] for p in ps)/len(ps))],
   'worst':[round(v) for v in pos(*worst)],'worst_swim_m':None if dist.get(worst) is None else round(dist[worst]/100,1),'component':comp[worst]})
 R['no_exit_clusters']=sorted(clusters,key=lambda c:-c['shore_samples'])
 R['exit_kinds']=collections.Counter(e[0] for e in exits.values())
 R['exit_landings']=collections.Counter(e[2] for e in exits.values()).most_common(15)
 R['exits']=[[k[0],k[1]]+v+[comp[k]] for k,v in sorted(exits.items())]
 R['seconds']=round(time.time()-t0);R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
